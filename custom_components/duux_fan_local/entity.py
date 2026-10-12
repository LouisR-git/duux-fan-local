"""Base entity for the Duux Fan Local integration."""

from __future__ import annotations

from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, MANUFACTURER, MODELS
from .mqtt import DuuxMqttClient


class DuuxEntity(Entity):
    """Common base entity for all Duux entities."""

    _attr_should_poll = False

    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        model: str,
    ) -> None:
        """Initialize the base entity."""
        self._client = client
        self._device_id = device_id
        self._name = base_name
        self._model = model

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information for grouping in Home Assistant."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._name,
            "manufacturer": MANUFACTURER,
            "model": MODELS.get(self._model, self._model),
            "connections": {("mac", self._device_id)},
        }

    async def _async_publish(self, payload: str) -> None:
        """Publish a command to the MQTT command topic."""
        await self.hass.async_add_executor_job(self._client.publish, payload)

    @callback
    def _update_state(self, device_data: dict[str, Any]) -> None:
        """Update entity state from parsed MQTT data."""
        raise NotImplementedError

    async def async_added_to_hass(self) -> None:
        """Register MQTT state callback when entity is added to Home Assistant."""
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister MQTT state callback when entity is removed."""
        self._client.unregister_callback(self._update_state)
