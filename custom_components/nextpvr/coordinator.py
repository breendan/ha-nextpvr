import asyncio
import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .nextpvr_api import NextPVRApi

_LOGGER = logging.getLogger(__name__)

class NextPVRDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, host, pin, port, use_ssl, update_interval):
        """Initialize the NextPVR coordinator."""
        session = async_get_clientsession(hass)
        self.api = NextPVRApi(session, host, pin, port=port, use_ssl=use_ssl)

        super().__init__(hass, _LOGGER, name="NextPVR Data Coordinator", update_interval=update_interval)

        # Kick off login early (non-blocking)
        asyncio.create_task(self._ensure_login())

    async def _ensure_login(self):
        """Login to NextPVR once at startup (non-blocking)."""
        try:
            await self.api.ensure_logged_in()
        except Exception as e:
            _LOGGER.warning(f"NextPVR initial login failed: {e}")

    async def _async_update_data(self):
        """Fetch device list and usage status from NextPVR."""
        try:
            devices = await self.api.get_devices()
            in_use = await self.api.devices_in_use()

            # Attach usage status to devices
            for device in devices:
                device_id = device.get("oid")
                device["is_in_use"] = device_id in in_use

            return {
                "devices": devices,                  # Full device list with is_in_use flag
                "in_use_ids": list(in_use.keys()),   # Flat list of active device oids
            }

        except Exception as err:
            raise HomeAssistantError(f"Error fetching data from NextPVR: {err}")
