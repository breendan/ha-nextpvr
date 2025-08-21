import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, CONF_HOST, CONF_PIN, CONF_PORT, CONF_SSL, DEFAULT_PORT, DEFAULT_SSL
from .coordinator import NextPVRDataUpdateCoordinator

PLATFORMS = ["binary_sensor", "media_player"]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NextPVR from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    host = entry.data[CONF_HOST]
    pin = entry.data[CONF_PIN]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    use_ssl = entry.data.get(CONF_SSL, DEFAULT_SSL)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Pass the configured scan interval into the coordinator
    coordinator = NextPVRDataUpdateCoordinator(hass, host, pin, port, use_ssl, update_interval=timedelta(seconds=scan_interval))
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    # Forward setup to each platform (binary_sensor, media_player)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for option changes
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update for scan interval."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: NextPVRDataUpdateCoordinator = data["coordinator"]

    new_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator.update_interval = timedelta(seconds=new_interval)

    _LOGGER.info("Updated scan interval to %s seconds", new_interval)

    # Optional: trigger an immediate refresh
    await coordinator.async_request_refresh()

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
