from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ATTR_NIGHT_MODE,
    ATTR_CHILD_LOCK,
)

from .mqtt import DuuxMqttClient

SWITCH_TYPES = {
    "night_mode": {
        "name": "Night Mode",
        "command_on": "tune set night 1",
        "command_off": "tune set night 0",
        "state_key": ATTR_NIGHT_MODE,
        "icon": "mdi:weather-night",
        "entity_category": None,
    },
    "child_lock": {
        "name": "Child Lock",
        "command_on": "tune set lock 1",
        "command_off": "tune set lock 0",
        "state_key": ATTR_CHILD_LOCK,
        "icon": "mdi:account-lock",
        "entity_category": EntityCategory.CONFIG,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Duux Fan switches from a config entry."""
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    base_name = config_entry.data["name"]
    device_id = config_entry.data["device_id"]

    switches = [
        DuuxSwitch(client, device_id, base_name, switch_type, details)
        for switch_type, details in SWITCH_TYPES.items()
    ]

    async_add_entities(switches)


class DuuxSwitch(SwitchEntity):
    """Representation of a Duux Fan switch."""

    _attr_should_poll = False

    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        switch_type: str,
        details: dict,
    ) -> None:
        """Initialize the switch."""
        self._client = client
        self._details = details
        self._attr_name = f"{base_name} {details['name']}"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{switch_type}"
        self.entity_id = f"switch.{self._attr_name.lower().replace(' ', '_')}"
        self._attr_is_on = False
        self._attr_icon = details["icon"]
        self._attr_entity_category = details["entity_category"]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_publish(self._details["command_on"])

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_publish(self._details["command_off"])

    async def _async_publish(self, payload: str) -> None:
        """Publish a command to the MQTT topic."""
        await self.hass.async_add_executor_job(self._client.publish, payload)

    @callback
    def _update_state(self, fan_data: dict) -> None:
        """Update the entity's state from parsed MQTT data."""
        state_key = self._details["state_key"]
        self._attr_is_on = fan_data.get(state_key, 0) > 0
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Run when entity is about to be added."""
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed."""
        self._client.unregister_callback(self._update_state)
