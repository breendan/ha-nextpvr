import logging
from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerState
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    data = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = data["coordinator"]
    entities = []

    for device in coordinator.data.get("devices", []):
        entities.append(NextPVRMediaPlayer(coordinator, device["oid"], device["identifier"]))

    async_add_entities(entities)

class NextPVRMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    _attr_should_poll = False

    def __init__(self, coordinator, device_oid, identifier):
        super().__init__(coordinator)
        self._device_oid = device_oid
        self._attr_unique_id = f"nextpvr_tuner_{device_oid}"
        self._attr_name = f"NextPVR Tuner {identifier}"

    def _device(self):
        # Always fetch fresh device state from coordinator
        return next((d for d in self.coordinator.data.get("devices", []) if d["oid"] == self._device_oid), {})

    @property
    def supported_features(self):
        # Return an iterable (set) for compatibility with HA expecting `FEATURE in supported_features`
        # No features exposed currently.
        return set()

    @property
    def state(self):
        status = self._device().get("status", "").lower()
        if status in ("livetv", "recording"):
            return MediaPlayerState.PLAYING
        if status == "idle":
            return MediaPlayerState.IDLE
        return MediaPlayerState.OFF

    @property
    def extra_state_attributes(self):
        device = self._device()
        return {
            "oid": self._device_oid,
            "status": device.get("status"),
            "path": device.get("path"),
        }

    @property
    def media_title(self):
        path = self._device().get("path", "")
        status = self._device().get("status", "").lower()

        if not path:
            return "Idle"

        filename = path.split("/")[-1].replace(".ts", "").strip()

        # Case 1: Live TV (e.g., live-TV channel-157-16.ts)
        if status == "livetv" and filename.startswith("live-"):
            parts = filename.split("-")
            if len(parts) >= 2:
                title = parts[1]
            else:
                title = filename
        else:
            # Case 2: Recording
            # Example: Show.Highlights.S2025E404.Round.2.-.Sport.Round.2
            title = filename.split(".-.")[0]  # Remove tailing duplicate info if present

        # Final cleanup: replace . and - with space, strip extra whitespace
        clean_title = title.replace(".", " ").replace("-", " ").strip()

        return clean_title or "Unknown"
