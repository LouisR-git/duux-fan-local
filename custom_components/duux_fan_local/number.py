from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import UnitOfTime

from .const import (
    DOMAIN,
    ATTR_TIMER,
    MAX_TIMER,
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
    base_name = config_entry.data["name"]
    device_id = config_entry.data["device_id"]

    entities = [
        DuuxTimerNumber(client, device_id, base_name),
        DuuxHorizontalOscillationNumber(client, device_id, base_name),
        DuuxVerticalOscillationNumber(client, device_id, base_name)
    ]
    async_add_entities(entities)


class DuuxTimerNumber(NumberEntity):
    """Representation of a Duux Fan timer."""

    _attr_should_poll = False
    _attr_native_min_value = 0.0
    _attr_native_max_value = float(MAX_TIMER)
    _attr_native_step = 1.0
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_icon = "mdi:timer-outline"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, client: DuuxMqttClient, device_id: str, base_name: str):
        """Initialize the number entity."""
        self._client = client
        self._attr_name = f"{base_name} Timer"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_timer"
        self.entity_id = f"number.{self._attr_name.lower().replace(' ', '_')}"
        self._attr_native_value = 0.0

    async def async_set_native_value(self, value: float) -> None:
        """Set the timer value."""
        timer_hours = int(round(value))
        await self._async_publish(f"tune set timer {timer_hours}")

    async def _async_publish(self, payload: str):
        """Publish a command to the MQTT topic."""
        await self.hass.async_add_executor_job(self._client.publish, payload)

    @callback
    def _update_state(self, fan_data: dict):
        """Update the entity's state from parsed MQTT data."""
        self._attr_native_value = float(fan_data.get(ATTR_TIMER, 0))
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed."""
        self._client.unregister_callback(self._update_state)


class DuuxHorizontalOscillationNumber(NumberEntity):
    """Representation of a Duux Fan Horizontal Oscillation control."""

    _attr_should_poll = False
    _attr_native_min_value = 0.0
    _attr_native_max_value = float(MAX_HOR_OSC)
    _attr_native_step = 1.0
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:arrow-left-right"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, client: DuuxMqttClient, device_id: str, base_name: str):
        """Initialize the number entity."""
        self._client = client
        self._attr_name = f"{base_name} Horizontal Oscillation"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_horizontal_oscillation"
        self.entity_id = f"number.{self._attr_name.lower().replace(' ', '_')}"
        self._attr_native_value = 0.0

    async def async_set_native_value(self, value: float) -> None:
        """Set the horizontal oscillation value."""
        osc_value = int(round(value))
        await self._async_publish(f"tune set horosc {osc_value}")

    async def _async_publish(self, payload: str):
        """Publish a command to the MQTT topic."""
        await self.hass.async_add_executor_job(self._client.publish, payload)

    @callback
    def _update_state(self, fan_data: dict):
        """Update the entity's state from parsed MQTT data."""
        self._attr_native_value = float(fan_data.get(ATTR_HOR_OSC, 0))
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed."""
        self._client.unregister_callback(self._update_state)


class DuuxVerticalOscillationNumber(NumberEntity):
    """Representation of a Duux Fan Vertical Oscillation control."""

    _attr_should_poll = False
    _attr_native_min_value = 0.0
    _attr_native_max_value = float(MAX_VER_OSC)
    _attr_native_step = 1.0
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:arrow-up-down"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, client: DuuxMqttClient, device_id: str, base_name: str):
        """Initialize the number entity."""
        self._client = client
        self._attr_name = f"{base_name} Vertical Oscillation"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_vertical_oscillation"
        self.entity_id = f"number.{self._attr_name.lower().replace(' ', '_')}"
        self._attr_native_value = 0.0

    async def async_set_native_value(self, value: float) -> None:
        """Set the vertical oscillation value."""
        osc_value = int(round(value))
        await self._async_publish(f"tune set verosc {osc_value}")

    async def _async_publish(self, payload: str):
        """Publish a command to the MQTT topic."""
        await self.hass.async_add_executor_job(self._client.publish, payload)

    @callback
    def _update_state(self, fan_data: dict):
        """Update the entity's state from parsed MQTT data."""
        self._attr_native_value = float(fan_data.get(ATTR_VER_OSC, 0))
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added."""
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed."""
        self._client.unregister_callback(self._update_state)