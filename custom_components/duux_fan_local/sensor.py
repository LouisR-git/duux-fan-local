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
from homeassistant.const import PERCENTAGE

from .const import DOMAIN, MANUFACTURER, MODELS, ATTR_BATLVL
from .mqtt import DuuxMqttClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Duux Fan sensors from a config entry."""
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data["device_id"]
    base_name = config_entry.data["name"]
    model = config_entry.data["model"]

    sensors = [
        DuuxBatteryLevelSensor(
            client=client,
            device_id=device_id,
            base_name=base_name,
            model=model,
        ),
    ]
    async_add_entities(sensors)


class DuuxBatteryLevelSensor(SensorEntity):
    """Representation of a Duux Fan Battery Level sensor."""

    _attr_should_poll = False
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:battery"

    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        model: str,
    ) -> None:
        """Initialize the sensor."""
        self._client = client
        self._device_id = device_id
        self._name = base_name
        self._model = model

        self._attr_name = f"{base_name} Battery Level"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_battery_level"
        self.entity_id = f"sensor.{base_name.lower().replace(' ', '_')}_battery_level"
        self._attr_native_value = None

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information for the entity."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._name,
            "manufacturer": MANUFACTURER,
            "model": MODELS.get(self._model),
        }

    @callback
    def _update_state(self, fan_data: dict[str, Any]) -> None:
        """Update the entity's state from parsed MQTT data."""
        self._attr_native_value = fan_data.get(ATTR_BATLVL, 0) * 10
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed."""
        self._client.unregister_callback(self._update_state)
