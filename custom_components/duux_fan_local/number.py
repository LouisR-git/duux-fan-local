from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import UnitOfTime

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODELS,
    MODEL_V1,
    ATTR_TIMER,
    ATTR_SPEED,
    MAX_TIMER,
    MAX_SPEED_V1,
    MAX_SPEED_V2,
    ATTR_HOR_OSC,
    ATTR_VER_OSC,
    MAX_HOR_OSC,
    MAX_VER_OSC,
)
from .mqtt import DuuxMqttClient


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Duux Fan number platform."""
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data["device_id"]
    base_name = config_entry.data["name"]
    model = config_entry.data.get("model", "whisper_flex_2")  # Default to v2 for backward compatibility

    entities = [
        DuuxTimerNumber(client, device_id, base_name, model),
        DuuxSpeedNumber(client, device_id, base_name, model),
    ]
    async_add_entities(entities)


class DuuxBaseNumber(NumberEntity):
    """Base class for Duux number entities with shared device_info."""

    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        model: str,
    ):
        self._client = client
        self._device_id = device_id
        self._name = base_name
        self._model = model

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._name,
            "manufacturer": MANUFACTURER,
            "model": MODELS.get(self._model),
            "connections": {("mac", self._device_id)},
        }

    async def _async_publish(self, payload: str):
        """Publish a command to the MQTT topic."""
        await self.hass.async_add_executor_job(self._client.publish, payload)

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed."""
        self._client.unregister_callback(self._update_state)


class DuuxTimerNumber(DuuxBaseNumber):
    """Representation of a Duux Fan timer."""

    _attr_should_poll = False
    _attr_native_min_value = 0.0
    _attr_native_max_value = float(MAX_TIMER)
    _attr_native_step = 1.0
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_icon = "mdi:timer-outline"
    _attr_entity_category = None

    def __init__(self, client: DuuxMqttClient, device_id: str, base_name: str, model: str):
        super().__init__(client, device_id, base_name, model)
        self._attr_name = f"{base_name} Timer"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_timer"
        self.entity_id = f"number.{self._attr_name.lower().replace(' ', '_')}"
        self._attr_native_value = 0.0

    async def async_set_native_value(self, value: float) -> None:
        timer_hours = int(round(value))
        await self._async_publish(f"tune set timer {timer_hours}")

    @callback
    def _update_state(self, fan_data: dict):
        self._attr_native_value = float(fan_data.get(ATTR_TIMER, 0))
        self.async_write_ha_state()


class DuuxSpeedNumber(DuuxBaseNumber):
    """Representation of a Duux Fan speed control."""

    _attr_should_poll = False
    _attr_native_min_value = 1.0
    _attr_native_step = 1.0
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:speedometer"
    _attr_entity_category = None

    def __init__(self, client: DuuxMqttClient, device_id: str, base_name: str, model: str):
        super().__init__(client, device_id, base_name, model)
        self._attr_name = f"{base_name} Speed"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_speed"
        self.entity_id = f"number.{self._attr_name.lower().replace(' ', '_')}"
        self._attr_native_value = 1.0

        # Set max speed based on model
        if model == MODEL_V1:
            self._attr_native_max_value = float(MAX_SPEED_V1)
        else:
            self._attr_native_max_value = float(MAX_SPEED_V2)

    async def async_set_native_value(self, value: float) -> None:
        speed_value = int(round(value))
        await self._async_publish(f"tune set speed {speed_value}")

    @callback
    def _update_state(self, fan_data: dict):
        self._attr_native_value = float(fan_data.get(ATTR_SPEED, 0))
        self.async_write_ha_state()
