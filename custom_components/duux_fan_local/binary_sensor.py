import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODELS, ATTR_BATCHA
from .mqtt import DuuxMqttClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Duux Fan binary sensors from a config entry."""
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data["device_id"]
    base_name = config_entry.data["name"]
    model = config_entry.data.get("model", "whisper_flex_2")  # Default to v2 for backward compatibility

    binary_sensors = []

    # Only add binary sensor for V2 fans
    if model != MODEL_V1:
        sensors.append(
             DuuxChargingBinarySensor(client, device_id, base_name, model),
        )
    async_add_entities(binary_sensors)


class DuuxChargingBinarySensor(BinarySensorEntity):
    """Representation of a Duux Fan Battery Charging status binary sensor."""

    _attr_should_poll = False
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING
    _attr_icon = "mdi:battery-charging"

    def __init__(self, client: DuuxMqttClient, device_id: str, base_name: str, model: str):
        """Initialize the binary sensor."""
        self._client = client
        self._device_id = device_id
        self._name = base_name
        self._model = model

        self._attr_name = f"{base_name} Charging"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_charging"
        self.entity_id = f"binary_sensor.{self._attr_name.lower().replace(' ', '_')}"
        self._attr_is_on = False

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information for grouping in Home Assistant."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._name,
            "manufacturer": MANUFACTURER,
            "model": MODELS.get(self._model),
            "connections": {("mac", self._device_id)},
        }

    @callback
    def _update_state(self, fan_data: dict):
        """Update the entity's state from parsed MQTT data."""
        self._attr_is_on = fan_data.get(ATTR_BATCHA, 0) == 1
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed."""
        self._client.unregister_callback(self._update_state)
