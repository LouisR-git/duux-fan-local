from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ATTR_MODE
from .mqtt import DuuxMqttClient

MODE_OPTIONS = {
    "Fan": 0,
    "Natural": 1,
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Duux Fan select entity for mode."""
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    base_name = config_entry.data["name"]
    device_id = config_entry.data["device_id"]

    entity = DuuxFanModeSelect(client, device_id, base_name)
    async_add_entities([entity])


class DuuxFanModeSelect(SelectEntity):
    """Representation of Duux Fan mode select entity."""

    _attr_should_poll = False
    _attr_options = list(MODE_OPTIONS.keys())

    def __init__(self, client: DuuxMqttClient, device_id: str, base_name: str):
        """Initialize the select entity."""
        self._client = client
        self._attr_name = f"{base_name} Fan Mode"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_fan_mode"
        self.entity_id = f"select.{base_name.lower().replace(' ', '_')}_fan_mode"
        self._current_mode_value = 0  # Default to 'Fan'

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        for name, value in MODE_OPTIONS.items():
            if value == self._current_mode_value:
                return name
        return None

    async def async_select_option(self, option: str) -> None:
        """Handle user selecting a new option."""
        if option not in MODE_OPTIONS:
            return
        mode_value = MODE_OPTIONS[option]
        await self._async_publish(f"tune set mode {mode_value}")

    async def _async_publish(self, payload: str):
        """Publish a command to the MQTT topic."""
        await self.hass.async_add_executor_job(self._client.publish, payload)

    @callback
    def _update_state(self, fan_data: dict):
        """Update the entity's state from parsed MQTT data."""
        self._current_mode_value = fan_data.get(ATTR_MODE, 0)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register update callback."""
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        """Unregister update callback."""
        self._client.unregister_callback(self._update_state)
