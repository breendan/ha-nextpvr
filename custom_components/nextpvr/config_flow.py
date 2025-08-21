import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, CONF_HOST, CONF_PIN, CONF_PORT, CONF_SSL, DEFAULT_PORT, DEFAULT_SSL
from .nextpvr_api import NextPVRApi

_LOGGER = logging.getLogger(__name__)

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""

async def _test_connection(hass, host: str, pin: str, port: int, use_ssl: bool) -> None:
    """Test connection to NextPVR by attempting a login using shared session."""
    session = async_get_clientsession(hass)
    api = NextPVRApi(session, host, pin, port=port, use_ssl=use_ssl)
    try:
        await api.ensure_logged_in()
    except Exception as exc:
        raise CannotConnect from exc

class NextPVRConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NextPVR."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            pin = user_input[CONF_PIN]
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            use_ssl = user_input.get(CONF_SSL, DEFAULT_SSL)
            try:
                await _test_connection(self.hass, host, pin, port, use_ssl)
                # Determine final scheme used for unique_id
                scheme = "https" if use_ssl else "http"
                if "://" in host:
                    # If user typed scheme, trust that
                    scheme = host.split("://", 1)[0].lower()
                await self.async_set_unique_id(f"{scheme}://{host}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{scheme}://{host}:{port}",
                    data=user_input
                )
            except CannotConnect:
                _LOGGER.error("Unable to connect to NextPVR at %s:%s", host, port)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during NextPVR config flow")
                errors["base"] = "unknown"

        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PIN): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(int, vol.Range(min=1, max=65535)),
            vol.Optional(CONF_SSL, default=DEFAULT_SSL): bool,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NextPVROptionsFlowHandler(config_entry)

class NextPVROptionsFlowHandler(config_entries.OptionsFlow):
    """Handle NextPVR options flow (scan interval only)."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the NextPVR options."""
        errors: dict[str, str] = {}
        current_scan = self._config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        if user_input is not None:
            # Validate connectivity (optional safety)
            host = self._config_entry.data.get(CONF_HOST)
            pin = self._config_entry.data.get(CONF_PIN)
            port = self._config_entry.data.get(CONF_PORT, DEFAULT_PORT)
            use_ssl = self._config_entry.data.get(CONF_SSL, DEFAULT_SSL)
            try:
                await _test_connection(self.hass, host, pin, port, use_ssl)
                return self.async_create_entry(
                    title="",
                    data={CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL]},
                )
            except CannotConnect:
                _LOGGER.error("Unable to connect to NextPVR at %s:%s during options save", host, port)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Error saving NextPVR options")
                errors["base"] = "unknown"

        schema = vol.Schema({
            vol.Required(CONF_SCAN_INTERVAL, default=current_scan): vol.All(
                int, vol.Range(min=30, max=3600)
            )
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
