"""
Fan platform for the Duux Fan Local integration.
Dynamically creates a FanEntity based on the device profile capabilities.
"""

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

from .const import DOMAIN
from .devices import DEVICE_PROFILES, ATTR_POWER, ATTR_SPEED, ATTR_SWING, ATTR_TILT
from .entity import DuuxEntity
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
    model = config_entry.data.get("model", "whisper_flex_2")

    profile = DEVICE_PROFILES.get(model)
    if not profile or "fan" not in profile:
        _LOGGER.debug("Model %s does not support a fan entity.", model)
        return

    fan = [
        DuuxFan(client, device_id, base_name, model, profile),
    ]
    async_add_entities(fan)


class DuuxFan(DuuxEntity, FanEntity):
    """Representation of a Duux Fan."""

    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        model: str,
        profile: dict,
    ) -> None:
        """Initialize the fan entity."""
        super().__init__(client, device_id, base_name, model)
        self._profile = profile
        self._fan_profile = profile["fan"]

        self._attr_name = base_name
        self._attr_unique_id = f"{DOMAIN}_{device_id}_fan"
        self.entity_id = f"fan.{base_name.lower().replace(' ', '_')}"
        self._attr_is_on = False
        self._speed = 0
        self._oscillating = False
        self._direction = "forward"

        self._max_speed = self._fan_profile.get("max_speed", 100)
        self._speed_range = (1, self._max_speed)

        features = self._fan_profile.get("supported_features", [])
        supported_features = FanEntityFeature(0)
        if "turn_on" in features:
            supported_features |= FanEntityFeature.TURN_ON
        if "turn_off" in features:
            supported_features |= FanEntityFeature.TURN_OFF
        if "set_speed" in features:
            supported_features |= FanEntityFeature.SET_SPEED
        if "oscillate" in features:
            supported_features |= FanEntityFeature.OSCILLATE
        if "direction" in features:
            supported_features |= FanEntityFeature.DIRECTION

        self._attr_supported_features = supported_features

        # Determine keys for power and speed based on profile
        self._power_key = self._fan_profile.get("power_key", ATTR_POWER)
        self._speed_key = self._fan_profile.get("speed_key", ATTR_SPEED)

    @property
    def is_on(self) -> bool:
        return self._attr_is_on

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        return (
            ranged_value_to_percentage(self._speed_range, self._speed)
            if self._speed
            else 0
        )

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
        if "oscillate" in self._fan_profile.get("supported_features", []):
            await self._async_publish(f"tune set swing {1 if oscillating else 0}")

    async def async_set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        if "direction" in self._fan_profile.get("supported_features", []):
            tilt_value = 1 if direction == "reverse" else 0
            await self._async_publish(f"tune set tilt {tilt_value}")

    @callback
    def _update_state(self, device_data: dict[str, Any]) -> None:
        """Update the entity's state from parsed MQTT data."""
        self._attr_is_on = device_data.get(self._power_key) == 1
        self._speed = device_data.get(self._speed_key, 0)

        if "oscillate" in self._fan_profile.get("supported_features", []):
            self._oscillating = device_data.get(ATTR_SWING, 0) == 1

        if "direction" in self._fan_profile.get("supported_features", []):
            self._direction = (
                "reverse" if device_data.get(ATTR_TILT, 0) == 1 else "forward"
            )

        self.async_write_ha_state()
