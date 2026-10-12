"""
Switch platform for the Duux Fan Local integration.
Dynamically creates SwitchEntities (e.g., Night Mode, ION) based on the device profile.
"""

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .devices import DEVICE_PROFILES
from .entity import DuuxEntity
from .mqtt import DuuxMqttClient


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Duux switches from a config entry."""
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data["device_id"]
    base_name = config_entry.data["name"]
    model = config_entry.data.get("model", "whisper_flex_2")

    profile = DEVICE_PROFILES.get(model)
    if not profile or "switches" not in profile:
        return

    switches = []
    for switch_id, details in profile["switches"].items():
        switches.append(
            DuuxSwitch(client, device_id, base_name, model, switch_id, details)
        )

    async_add_entities(switches)


class DuuxSwitch(DuuxEntity, SwitchEntity):
    """Representation of a Duux switch."""

    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        model: str,
        switch_id: str,
        details: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        super().__init__(client, device_id, base_name, model)
        self._details = details
        self._switch_id = switch_id

        self._attr_name = f"{base_name} {details['name']}"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{switch_id}"
        self.entity_id = f"switch.{self._attr_name.lower().replace(' ', '_')}"
        self._attr_is_on = False
        self._attr_icon = details.get("icon")
        self._attr_entity_category = details.get("entity_category")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_publish(self._details["command_on"])

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_publish(self._details["command_off"])

    @callback
    def _update_state(self, device_data: dict[str, Any]) -> None:
        """Update the entity's state from parsed MQTT data."""
        state_key = self._details["state_key"]
        self._attr_is_on = device_data.get(state_key, 0) > 0
        self.async_write_ha_state()
