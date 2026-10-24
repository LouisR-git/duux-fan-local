from unittest.mock import patch

import pytest
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.duux_fan_local.const import DOMAIN
from custom_components.duux_fan_local import async_migrate_entry, async_setup_entry


async def test_async_migrate_entry_v1_to_v2(hass):
    """Test successful migration of a config entry from version 1 to version 2."""

    # Create a mock config entry for Version 1
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={
            "device_id": "aa:bb:cc:dd:ee:ff",
            "name": "My Old Whisper Fan",
            # Notice "model" is missing, representing a very old V1 config
        },
    )

    # Add it to hass
    config_entry.add_to_hass(hass)

    # Perform the migration
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_update_entry"
    ) as mock_update:
        # Mock the async_update_entry behavior to actually update the object
        def update_mock(entry, data=None, version=None, *args, **kwargs):
            if data is not None:
                entry.data = data
            if version is not None:
                entry.version = version

        mock_update.side_effect = update_mock

        result = await async_migrate_entry(hass, config_entry)

        # Ensure migration was successful
        assert result is True
        # Ensure version is bumped
        assert config_entry.version == 2
        # Ensure default model is added if requested
        assert "model" in config_entry.data
        assert config_entry.data["model"] == "whisper_flex_2"
        assert config_entry.data["use_tls"] is False
        # Ensure previous data is preserved
        assert config_entry.data["device_id"] == "aa:bb:cc:dd:ee:ff"
        assert config_entry.data["name"] == "My Old Whisper Fan"


async def test_async_migrate_entry_already_v2(hass):
    """Test that migration does not modify an already v2 config entry."""

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={"device_id": "aa:bb:cc:dd", "name": "Bright 2", "model": "bright_2"},
    )

    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_update_entry"
    ) as mock_update:
        result = await async_migrate_entry(hass, config_entry)

        # Migration should just pass and return True
        assert result is True
        assert config_entry.version == 2

        # Ensure async_update_entry was NEVER called because no migration was needed
        mock_update.assert_not_called()


async def test_async_migrate_entry_dehumidifier_model_to_bora_smart(hass):
    """Test that model 'dehumidifier' is migrated to 'bora_smart'."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            "device_id": "aa:bb:cc:dd",
            "name": "Dehumidifier",
            "model": "dehumidifier",
        },
    )
    config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_update_entry"
    ) as mock_update:

        def update_mock(entry, data=None, version=None, *args, **kwargs):
            if data is not None:
                entry.data = data
            if version is not None:
                entry.version = version

        mock_update.side_effect = update_mock

        result = await async_migrate_entry(hass, config_entry)

        assert result is True
        assert config_entry.data["model"] == "bora_smart"
        mock_update.assert_called_once()


async def test_async_setup_entry_raises_config_entry_not_ready_on_oserror(hass):
    """Test async_setup_entry raises ConfigEntryNotReady when broker connection fails."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            "device_id": "aa:bb:cc:dd:ee:ff",
            "name": "Bright 2",
            "model": "bright_2",
        },
    )
    config_entry.add_to_hass(hass)

    with patch(
        "custom_components.duux_fan_local.mqtt.DuuxMqttClient.async_connect",
        side_effect=OSError("Broker unreachable"),
    ):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, config_entry)


async def test_async_setup_entry_sets_use_tls_false_when_missing(hass):
    """Test async_setup_entry sets use_tls to False for legacy entries without use_tls."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        data={
            "device_id": "aa:bb:cc:dd:ee:ff",
            "name": "Living Room Fan",
            "model": "whisper_flex_2",
        },
    )
    config_entry.add_to_hass(hass)

    with (
        patch("custom_components.duux_fan_local.mqtt.DuuxMqttClient.async_connect"),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
            return_value=True,
        ),
    ):
        result = await async_setup_entry(hass, config_entry)
        assert result is True
        assert config_entry.data["use_tls"] is False
