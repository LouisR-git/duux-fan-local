from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODELS,
    MODEL_V1,
    ATTR_NIGHT_MODE,
    ATTR_CHILD_LOCK,
    ATTR_SWING,
    ATTR_TILT,
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
        "entity_category": None,
    },
    "horizontal_oscillation_v1": {
        "name": "Horizontal Oscillation",
        "command_on": "tune set swing 1",
        "command_off": "tune set swing 0",
        "state_key": ATTR_SWING,
        "icon": "mdi:arrow-left-right",
        "entity_category": None,
        "model_specific": MODEL_V1,
    },
    "vertical_oscillation_v1": {
        "name": "Vertical Oscillation",
        "command_on": "tune set tilt 1",
        "command_off": "tune set tilt 0",
        "state_key": ATTR_TILT,
        "icon": "mdi:arrow-up-down",
        "entity_category": None,
        "model_specific": MODEL_V1,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Duux Fan switches from a config entry."""
    client: DuuxMqttClient = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data["device_id"]
    base_name = config_entry.data["name"]
    model = config_entry.data.get(
        "model", "whisper_flex_2"
    )  # Default to v2 for backward compatibility

    switches = []

    # Only add switches that are supported by the model
    for switch_type, details in SWITCH_TYPES.items():
        # Skip child lock and night mode for V1 fans
        if model == MODEL_V1 and switch_type in ["child_lock", "night_mode"]:
            continue

        # Only add V1 specific oscillation switches for V1 model
        if switch_type in ["horizontal_oscillation_v1", "vertical_oscillation_v1"]:
            if model != MODEL_V1:
                continue

        # Only add V2 specific switches for V2 model (none currently, but structure for future)
        if "model_specific" in details and details["model_specific"] != model:
            continue

        switches.append(
            DuuxSwitch(client, device_id, base_name, model, switch_type, details)
        )

    async_add_entities(switches)


class DuuxSwitch(SwitchEntity):
    """Representation of a Duux Fan switch."""

    _attr_should_poll = False

    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        model: str,
        switch_type: str,
        details: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        self._client = client
        self._details = details
        self._device_id = device_id
        self._name = base_name
        self._model = model
        self._switch_type = switch_type

        self._attr_name = f"{base_name} {details['name']}"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{switch_type}"
        self.entity_id = f"switch.{self._attr_name.lower().replace(' ', '_')}"
        self._attr_is_on = False
        self._attr_icon = details["icon"]
        self._attr_entity_category = details["entity_category"]

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information for grouping in Home Assistant."""
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._name,
            "manufacturer": MANUFACTURER,
            "model": MODELS.get(self._model),
            "connections": {("mac", self._device_id)},
        }

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
    def _update_state(self, fan_data: dict[str, Any]) -> None:
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
