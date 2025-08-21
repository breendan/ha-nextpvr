from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    async_add_entities([NextPVRDeviceInUseBinarySensor(coordinator, entry.entry_id)], True)

class NextPVRDeviceInUseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for whether any NextPVR device is in use."""

    def __init__(self, coordinator, entry_id):
        super().__init__(coordinator)
        self._attr_name = "NextPVR Device In Use"
        self._attr_device_class = "running"
        self._attr_unique_id = f"{entry_id}_running"

    @property
    def is_on(self):
        """Return True if any device is active."""
        in_use_ids = self.coordinator.data.get("in_use_ids", [])
        return len(in_use_ids) > 0

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        return {
            "in_use_device_ids": self.coordinator.data.get("in_use_ids", []),
        }
