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
    ATTR_POWER,
    ATTR_SPEED,
    MAX_SPEED,
)
from .mqtt import DuuxMqttClient

_LOGGER = logging.getLogger(__name__)

SPEED_RANGE = (1, MAX_SPEED)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Duux Fan from a config entry."""
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data["device_id"]
    base_name = config_entry.data["name"]
    model = config_entry.data["model"]

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

        self._attr_supported_features = (
            FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF
            | FanEntityFeature.SET_SPEED
        )

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
        return ranged_value_to_percentage(SPEED_RANGE, self._speed)

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
        speed = round(percentage_to_ranged_value(SPEED_RANGE, percentage))
        await self._async_publish(f"tune set speed {speed}")

    async def _async_publish(self, payload: str) -> None:
        """Publish a command to the MQTT topic."""
        await self.hass.async_add_executor_job(self._client.publish, payload)

    @callback
    def _update_state(self, fan_data: dict[str, Any]) -> None:
        """Update the entity's state from parsed MQTT data."""
        self._attr_is_on = fan_data.get(ATTR_POWER) == 1
        self._speed = fan_data.get(ATTR_SPEED)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to Home Assistant."""
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity is removed from Home Assistant."""
        self._client.unregister_callback(self._update_state)
