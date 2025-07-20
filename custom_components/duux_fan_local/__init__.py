from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN
from .mqtt import DuuxMqttClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.FAN,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.BINARY_SENSOR,
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Duux Fan from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create and connect the MQTT client
    client = DuuxMqttClient(hass, entry.data)
    # The connect call is blocking, so it must be run in an executor
    await hass.async_add_executor_job(client.connect)

    hass.data[DOMAIN][entry.entry_id] = client

    # Forward the setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        client: DuuxMqttClient = hass.data[DOMAIN].pop(entry.entry_id)
        # The disconnect call is blocking, so it must be run in an executor
        await hass.async_add_executor_job(client.disconnect)

    return unload_ok