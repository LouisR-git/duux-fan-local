"""
The Duux Fan Local integration.
This module sets up the integration and handles the migration of older configuration entries.
"""

from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_USE_TLS, DOMAIN
from .mqtt import DuuxMqttClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.FAN,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.SELECT,
    Platform.BINARY_SENSOR,
    Platform.HUMIDIFIER,
    Platform.CLIMATE,
]


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        new_data = {**config_entry.data}
        # Ensure model is set if it was missing in very old entries
        if "model" not in new_data:
            new_data["model"] = "whisper_flex_2"
        if CONF_USE_TLS not in new_data:
            new_data[CONF_USE_TLS] = False

        hass.config_entries.async_update_entry(config_entry, data=new_data, version=2)

    if config_entry.data.get("model") == "dehumidifier":
        new_data = {**config_entry.data, "model": "bora_smart"}
        hass.config_entries.async_update_entry(config_entry, data=new_data)

    _LOGGER.info("Migration to version %s successful", config_entry.version)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Duux Fan from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    if CONF_USE_TLS not in entry.data:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_USE_TLS: False}
        )

    # Create and connect the MQTT client
    client = DuuxMqttClient(hass, entry.data)
    try:
        await client.async_connect()
    except OSError as err:
        raise ConfigEntryNotReady(
            f"Failed to connect to Duux MQTT broker: {err}"
        ) from err

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
