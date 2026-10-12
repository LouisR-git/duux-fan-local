"""
Binary sensor platform for the Duux Fan Local integration.
Dynamically creates BinarySensorEntities based on the device profile.
"""

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
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
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data["device_id"]
    base_name = config_entry.data["name"]
    model = config_entry.data.get("model", "whisper_flex_2")

    profile = DEVICE_PROFILES.get(model)
    if not profile or "binary_sensors" not in profile:
        return

    binary_sensors = []
    for bs_id, details in profile["binary_sensors"].items():
        binary_sensors.append(
            DuuxBinarySensor(client, device_id, base_name, model, bs_id, details)
        )

    async_add_entities(binary_sensors)


class DuuxBinarySensor(DuuxEntity, BinarySensorEntity):
    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        model: str,
        bs_id: str,
        details: dict,
    ):
        super().__init__(client, device_id, base_name, model)
        self._bs_id = bs_id
        self._details = details

        self._attr_name = f"{base_name} {details['name']}"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{bs_id}"
        self.entity_id = f"binary_sensor.{self._attr_name.lower().replace(' ', '_')}"
        self._attr_is_on = False

        dc = details.get("device_class")
        if dc:
            self._attr_device_class = BinarySensorDeviceClass(dc)

        self._attr_icon = details.get("icon")

    @callback
    def _update_state(self, device_data: dict[str, Any]):
        state_key = self._details.get("state_key")
        val = device_data.get(state_key)
        if val is not None:
            on_value = self._details.get("on_value", 1)
            self._attr_is_on = val == on_value
            self.async_write_ha_state()
