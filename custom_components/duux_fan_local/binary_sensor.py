import logging

"""
Binary sensor platform for the Duux Fan Local integration.
Dynamically creates BinarySensorEntities based on the device profile.
"""
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODELS
from .devices import DEVICE_PROFILES
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


class DuuxBinarySensor(BinarySensorEntity):
    _attr_should_poll = False

    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        model: str,
        bs_id: str,
        details: dict,
    ):
        self._client = client
        self._device_id = device_id
        self._name = base_name
        self._model = model
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

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._name,
            "manufacturer": MANUFACTURER,
            "model": MODELS.get(self._model, self._model),
            "connections": {("mac", self._device_id)},
        }

    @callback
    def _update_state(self, fan_data: dict):
        state_key = self._details.get("state_key")
        val = fan_data.get(state_key)
        if val is not None:
            self._attr_is_on = val == 1
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        self._client.unregister_callback(self._update_state)
