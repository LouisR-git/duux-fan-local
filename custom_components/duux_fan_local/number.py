"""
Number platform for the Duux Fan Local integration.
Dynamically creates NumberEntities (e.g., Speed slider) based on the device profile.
"""

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import UnitOfTime

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
    if not profile or "numbers" not in profile:
        return

    entities = []
    for number_id, details in profile["numbers"].items():
        entities.append(
            DuuxNumber(client, device_id, base_name, model, number_id, details)
        )

    async_add_entities(entities)


class DuuxNumber(NumberEntity):
    _attr_should_poll = False
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        client: DuuxMqttClient,
        device_id: str,
        base_name: str,
        model: str,
        number_id: str,
        details: dict,
    ):
        self._client = client
        self._device_id = device_id
        self._name = base_name
        self._model = model
        self._number_id = number_id
        self._details = details

        self._attr_name = f"{base_name} {details['name']}"
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{number_id}"
        self.entity_id = f"number.{self._attr_name.lower().replace(' ', '_')}"

        self._attr_native_min_value = float(details.get("min", 1.0))
        self._attr_native_max_value = float(details.get("max", 100.0))
        self._attr_native_step = float(details.get("step", 1.0))

        if details.get("unit"):
            if details["unit"] == "h":
                self._attr_native_unit_of_measurement = UnitOfTime.HOURS
            else:
                self._attr_native_unit_of_measurement = details["unit"]

        self._attr_icon = details.get("icon")
        self._attr_native_value = self._attr_native_min_value

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._device_id)},
            "name": self._name,
            "manufacturer": MANUFACTURER,
            "model": MODELS.get(self._model, self._model),
            "connections": {("mac", self._device_id)},
        }

    async def async_set_native_value(self, value: float) -> None:
        cmd_topic = self._details.get("command_topic")
        if cmd_topic:
            val = int(round(value))
            await self.hass.async_add_executor_job(
                self._client.publish, f"{cmd_topic} {val}"
            )

    @callback
    def _update_state(self, fan_data: dict):
        state_key = self._details.get("state_key")
        val = fan_data.get(state_key)
        if val is not None:
            self._attr_native_value = float(val)
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._client.register_callback(self._update_state)

    async def async_will_remove_from_hass(self) -> None:
        self._client.unregister_callback(self._update_state)
