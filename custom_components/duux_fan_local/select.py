from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODELS,
    MODEL_V1,
    ATTR_MODE,
    ATTR_HOR_OSC,
    ATTR_VER_OSC,
    ATTR_SWING,
    ATTR_TILT,
    V1_MODE_OPTIONS,
    V2_MODE_OPTIONS,
    V1_HOR_OSC_OPTIONS,
    V2_HOR_OSC_OPTIONS,
    V1_VER_OSC_OPTIONS,
    V2_VER_OSC_OPTIONS,
)
from .mqtt import DuuxMqttClient


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Duux Fan select entities."""
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data["device_id"]
    base_name = config_entry.data["name"]
    model = config_entry.data.get(
        "model", "whisper_flex_2"
    )  # Default to v2 for backward compatibility

    entities = [
        DuuxFanModeSelect(client, device_id, base_name, model),
    ]

    # Only add oscillation select entities for V2 fans
    # V1 fans use switch entities for oscillation instead
    if model != MODEL_V1:
        entities.extend(
            [
                DuuxHorizontalOscillationSelect(client, device_id, base_name, model),
                DuuxVerticalOscillationSelect(client, device_id, base_name, model),
            ]
        )

    async_add_entities(entities)


class DuuxBaseSelect(SelectEntity):
    """Base class for Duux select entities with shared device_info."""

    def __init__(
        self, client: DuuxMqttClient, device_id: str, base_name: str, model: str
    ):
        self._client = client
        self._device_id = device_id
        self._name = base_name
        self._model = model

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._name,
            "manufacturer": MANUFACTURER,
            "model": MODELS.get(self._model),
            "connections": {("mac", self._device_id)},
        }

    async def _async_publish(self, payload: str) -> None:
        await self.hass.async_add_executor_job(self._client.publish, payload)

    async def async_added_to_hass(self) -> None:
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        self._client.unregister_callback(self._update_state)


class DuuxFanModeSelect(DuuxBaseSelect):
    _attr_should_poll = False
    _attr_icon = "mdi:weather-windy"

    def __init__(self, client, device_id, base_name, model):
        super().__init__(client, device_id, base_name, model)
        self._attr_name = f"{base_name} Fan Mode"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_fan_mode"
        self.entity_id = f"select.{base_name.lower().replace(' ', '_')}_fan_mode"
        self._current_mode_value = 0

        # Set mode options based on model
        if model == MODEL_V1:
            self._mode_options = V1_MODE_OPTIONS
        else:
            self._mode_options = V2_MODE_OPTIONS

        self._attr_options = list(self._mode_options.keys())

    @property
    def current_option(self) -> str | None:
        return next(
            (k for k, v in self._mode_options.items() if v == self._current_mode_value),
            None,
        )

    async def async_select_option(self, option: str) -> None:
        if option in self._mode_options:
            await self._async_publish(f"tune set mode {self._mode_options[option]}")

    @callback
    def _update_state(self, fan_data: dict[str, Any]) -> None:
        self._current_mode_value = fan_data.get(ATTR_MODE, 0)
        self.async_write_ha_state()


class DuuxHorizontalOscillationSelect(DuuxBaseSelect):
    _attr_should_poll = False
    _attr_icon = "mdi:arrow-left-right"

    def __init__(self, client, device_id, base_name, model):
        super().__init__(client, device_id, base_name, model)
        self._attr_name = f"{base_name} Horizontal Oscillation"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_horizontal_oscillation"
        self.entity_id = (
            f"select.{base_name.lower().replace(' ', '_')}_horizontal_oscillation"
        )
        self._current_value = 0

        # Set oscillation options and command based on model
        if model == MODEL_V1:
            self._osc_options = V1_HOR_OSC_OPTIONS
            self._command = "swing"  # V1 uses 'swing' instead of 'horosc'
        else:
            self._osc_options = V2_HOR_OSC_OPTIONS
            self._command = "horosc"

        self._attr_options = list(self._osc_options.keys())

    @property
    def current_option(self) -> str | None:
        return next(
            (k for k, v in self._osc_options.items() if v == self._current_value), None
        )

    async def async_select_option(self, option: str) -> None:
        if option in self._osc_options:
            await self._async_publish(
                f"tune set {self._command} {self._osc_options[option]}"
            )

    @callback
    def _update_state(self, fan_data: dict[str, Any]) -> None:
        # Use appropriate state key based on model
        if self._model == MODEL_V1:
            self._current_value = fan_data.get(ATTR_SWING, 0)
        else:
            self._current_value = fan_data.get(ATTR_HOR_OSC, 0)
        self.async_write_ha_state()


class DuuxVerticalOscillationSelect(DuuxBaseSelect):
    _attr_should_poll = False
    _attr_icon = "mdi:arrow-up-down"

    def __init__(self, client, device_id, base_name, model):
        super().__init__(client, device_id, base_name, model)
        self._attr_name = f"{base_name} Vertical Oscillation"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_vertical_oscillation"
        self.entity_id = (
            f"select.{base_name.lower().replace(' ', '_')}_vertical_oscillation"
        )
        self._current_value = 0

        # Set oscillation options and command based on model
        if model == MODEL_V1:
            self._osc_options = V1_VER_OSC_OPTIONS
            self._command = "tilt"  # V1 uses 'tilt' instead of 'verosc'
        else:
            self._osc_options = V2_VER_OSC_OPTIONS
            self._command = "verosc"

        self._attr_options = list(self._osc_options.keys())

    @property
    def current_option(self) -> str | None:
        return next(
            (k for k, v in self._osc_options.items() if v == self._current_value), None
        )

    async def async_select_option(self, option: str) -> None:
        if option in self._osc_options:
            await self._async_publish(
                f"tune set {self._command} {self._osc_options[option]}"
            )

    @callback
    def _update_state(self, fan_data: dict[str, Any]) -> None:
        # Use appropriate state key based on model
        if self._model == MODEL_V1:
            self._current_value = fan_data.get(ATTR_TILT, 0)
        else:
            self._current_value = fan_data.get(ATTR_VER_OSC, 0)
        self.async_write_ha_state()
