import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODELS,
    CONF_DEVICE_ID,
    MODEL_V1,
    ATTR_POWER,
    ATTR_SPEED,
    ATTR_SWING,
    ATTR_TILT,
    MAX_SPEED_V1,
    MAX_SPEED_V2,
)
from .mqtt import DuuxMqttClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Duux Fan from a config entry."""
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data["device_id"]
    base_name = config_entry.data["name"]
    model = config_entry.data.get("model", "whisper_flex_2")  # Default to v2 for backward compatibility

    fan = [
        DuuxFan(client, device_id, base_name, model),
    ]
    async_add_entities(fan)


class DuuxFan(FanEntity):
    """Representation of a Duux Fan."""

    _attr_should_poll = False

    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        model: str,
    ) -> None:
        """Initialize the fan entity."""
        self._client = client
        self._name = base_name
        self._device_id = device_id
        self._model = model

        self._attr_name = base_name
        self._attr_unique_id = f"{DOMAIN}_{device_id}_fan"
        self.entity_id = f"fan.{base_name.lower().replace(' ', '_')}"
        self._attr_is_on = False
        self._speed = 0
        self._oscillating = False
        self._direction = "forward"  # Default direction

        # Set speed range based on model
        self._max_speed = MAX_SPEED_V1 if model == MODEL_V1 else MAX_SPEED_V2
        self._speed_range = (1, self._max_speed)

        # Set supported features based on model
        supported_features = (
            FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.SET_SPEED
        )

        # V1 fans support simple oscillation and direction
        if model == MODEL_V1:
            supported_features |= FanEntityFeature.OSCILLATE | FanEntityFeature.DIRECTION

        self._attr_supported_features = supported_features

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info for the entity registry."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._name,
            "manufacturer": MANUFACTURER,
            "model": MODELS.get(self._model),
            "connections": {("mac", self._device_id)},
        }

    @property
    def is_on(self) -> bool:
        return self._attr_is_on

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        return ranged_value_to_percentage(self._speed_range, self._speed)

    @property
    def oscillating(self) -> bool:
        """Return whether or not the fan is currently oscillating."""
        return self._oscillating

    @property
    def current_direction(self) -> str:
        """Return the current direction of the fan."""
        return self._direction

    async def async_turn_on(self, *args, **kwargs) -> None:
        """Turn the fan on."""
        await self._async_publish("tune set power 1")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        await self._async_publish("tune set power 0")

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan."""
        if percentage == 0:
            await self.async_turn_off()
            return
        if not self._attr_is_on:
            await self._async_publish("tune set power 1")
        speed = round(percentage_to_ranged_value(self._speed_range, percentage))
        await self._async_publish(f"tune set speed {speed}")

    async def async_oscillate(self, oscillating: bool) -> None:
        """Turn oscillation on or off."""
        if self._model == MODEL_V1:
            # V1 fans use swing for horizontal oscillation
            await self._async_publish(f"tune set swing {1 if oscillating else 0}")
        # V2 fans don't support simple oscillation (they use select entities with angles)

    async def async_set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        if self._model == MODEL_V1:
            # V1 fans use tilt for vertical oscillation/direction
            # Map direction to tilt: forward = off, reverse = on
            tilt_value = 1 if direction == "reverse" else 0
            await self._async_publish(f"tune set tilt {tilt_value}")
        # V2 fans don't support simple direction (they use select entities with angles)

    async def _async_publish(self, payload: str) -> None:
        """Publish a command to the MQTT topic."""
        await self.hass.async_add_executor_job(self._client.publish, payload)

    @callback
    def _update_state(self, fan_data: dict[str, Any]) -> None:
        """Update the entity's state from parsed MQTT data."""
        self._attr_is_on = fan_data.get(ATTR_POWER) == 1
        self._speed = fan_data.get(ATTR_SPEED)

        # Update oscillation and direction state for V1 fans
        if self._model == MODEL_V1:
            # Swing represents horizontal oscillation
            self._oscillating = fan_data.get(ATTR_SWING, 0) == 1
            # Tilt represents vertical oscillation/direction
            self._direction = "reverse" if fan_data.get(ATTR_TILT, 0) == 1 else "forward"

        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to Home Assistant."""
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity is removed from Home Assistant."""
        self._client.unregister_callback(self._update_state)
