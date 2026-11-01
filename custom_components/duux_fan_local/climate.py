"""
Climate platform for the Duux Fan Local integration.
Provides local control of Duux heaters over MQTT.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
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
    """Set up Duux heater entities from a config entry."""
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data["device_id"]
    base_name = config_entry.data["name"]
    model = config_entry.data.get("model", "whisper_flex_2")

    profile = DEVICE_PROFILES.get(model)
    if not profile or "climate" not in profile:
        return

    async_add_entities(
        [
            DuuxHeater(
                client=client,
                device_id=device_id,
                base_name=base_name,
                model=model,
                details=profile["climate"],
            )
        ]
    )


class DuuxHeater(DuuxEntity, ClimateEntity):
    """Representation of a Duux heater."""

    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        model: str,
        details: dict[str, Any],
    ) -> None:
        """Initialize the heater."""
        super().__init__(client, device_id, base_name, model)
        self._details = details

        self._attr_name = base_name
        self._attr_unique_id = f"{DOMAIN}_{device_id}_climate"

        self._attr_hvac_mode = HVACMode.OFF
        self._attr_target_temperature = None
        self._attr_current_temperature = None

        self._attr_min_temp = float(details.get("min_temp", 5))
        self._attr_max_temp = float(details.get("max_temp", 36))
        self._attr_target_temperature_step = float(details.get("temp_step", 1))

    async def async_turn_on(self) -> None:
        """Turn the heater on."""
        await self._async_publish("tune set power 1")

    async def async_turn_off(self) -> None:
        """Turn the heater off."""
        await self._async_publish("tune set power 0")

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode (off or heat)."""
        if hvac_mode == HVACMode.HEAT:
            await self.async_turn_on()
        elif hvac_mode == HVACMode.OFF:
            await self.async_turn_off()
        else:
            _LOGGER.warning("Unsupported HVAC mode for Duux heater: %s", hvac_mode)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        step = self._attr_target_temperature_step
        temperature = round(temperature / step) * step
        temperature = max(self._attr_min_temp, min(self._attr_max_temp, temperature))
        await self._async_publish(f"tune set sp {int(temperature)}")

    @callback
    def _update_state(self, device_data: dict[str, Any]) -> None:
        """Update state from MQTT payload."""
        power_key = self._details.get("power_key", "power")
        target_key = self._details.get("target_temperature_key", "sp")
        current_key = self._details.get("current_temperature_key", "temp")

        power = device_data.get(power_key)
        target = device_data.get(target_key)
        current = device_data.get(current_key)

        if power is not None:
            self._attr_hvac_mode = HVACMode.HEAT if power == 1 else HVACMode.OFF

        if target is not None:
            self._attr_target_temperature = float(target)

        if current is not None:
            self._attr_current_temperature = float(current)

        self.async_write_ha_state()
