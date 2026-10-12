"""
Sensor platform for the Duux Fan Local integration.
Dynamically creates SensorEntities based on the device profile.
"""

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .devices import DEVICE_PROFILES
from .entity import DuuxEntity
from .mqtt import DuuxMqttClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Duux sensors from a config entry."""
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data["device_id"]
    base_name = config_entry.data["name"]
    model = config_entry.data.get("model", "whisper_flex_2")

    profile = DEVICE_PROFILES.get(model)
    if not profile or "sensors" not in profile:
        return

    sensors = []
    for sensor_id, details in profile["sensors"].items():
        sensors.append(
            DuuxSensor(client, device_id, base_name, model, sensor_id, details)
        )

    async_add_entities(sensors)


class DuuxSensor(DuuxEntity, SensorEntity):
    """Representation of a Duux Sensor."""

    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        model: str,
        sensor_id: str,
        details: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(client, device_id, base_name, model)
        self._sensor_id = sensor_id
        self._details = details

        self._attr_name = f"{base_name} {details['name']}"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{sensor_id}"
        self.entity_id = f"sensor.{self._attr_name.lower().replace(' ', '_')}"
        self._attr_native_value = None

        if "device_class" in details and details["device_class"]:
            self._attr_device_class = SensorDeviceClass(details["device_class"])
        if "state_class" in details and details["state_class"]:
            self._attr_state_class = getattr(
                SensorStateClass, details["state_class"].upper(), None
            )
        if "unit" in details and details["unit"]:
            self._attr_native_unit_of_measurement = details["unit"]
        if "icon" in details and details["icon"]:
            self._attr_icon = details["icon"]

    @callback
    def _update_state(self, device_data: dict[str, Any]) -> None:
        """Update the entity's state from parsed MQTT data."""
        state_key = self._details["state_key"]
        val = device_data.get(state_key)

        if val is not None:
            multiplier = self._details.get("multiplier", 1)
            self._attr_native_value = val * multiplier
            self.async_write_ha_state()
