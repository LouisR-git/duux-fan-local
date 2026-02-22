"""
Select platform for the Duux Fan Local integration.
Dynamically creates SelectEntities (e.g., Fan Mode) based on the device profile.
"""

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODELS
from .devices import DEVICE_PROFILES
from .mqtt import DuuxMqttClient


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data["device_id"]
    base_name = config_entry.data["name"]
    model = config_entry.data.get("model", "whisper_flex_2")

    profile = DEVICE_PROFILES.get(model)
    if not profile or "select" not in profile:
        return

    entities = []
    for select_id, details in profile["select"].items():
        entities.append(
            DuuxSelect(client, device_id, base_name, model, select_id, details)
        )

    async_add_entities(entities)


class DuuxSelect(SelectEntity):
    _attr_should_poll = False

    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        model: str,
        select_id: str,
        details: dict,
    ):
        self._client = client
        self._device_id = device_id
        self._name = base_name
        self._model = model
        self._select_id = select_id
        self._details = details

        self._attr_name = f"{base_name} {details['name']}"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{select_id}"
        self.entity_id = f"select.{self._attr_name.lower().replace(' ', '_')}"

        self._attr_icon = details.get("icon")
        self._options_map = details.get("options", {})
        self._attr_options = list(self._options_map.keys())
        self._current_val = None

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._name,
            "manufacturer": MANUFACTURER,
            "model": MODELS.get(self._model, self._model),
            "connections": {("mac", self._device_id)},
        }

    @property
    def current_option(self) -> str | None:
        if self._current_val is None:
            return None
        return next(
            (k for k, v in self._options_map.items() if v == self._current_val), None
        )

    async def async_select_option(self, option: str) -> None:
        if option in self._options_map:
            val = self._options_map[option]
            cmd = self._details.get("command_topic")
            if cmd:
                await self.hass.async_add_executor_job(
                    self._client.publish, f"{cmd} {val}"
                )

    @callback
    def _update_state(self, fan_data: dict[str, Any]) -> None:
        state_key = self._details.get("state_key")
        val = fan_data.get(state_key)
        if val is not None:
            self._current_val = val
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        self._client.unregister_callback(self._update_state)
