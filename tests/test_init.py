from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.duux_fan_local.const import DOMAIN
from custom_components.duux_fan_local import async_migrate_entry


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
        def update_mock(entry, data, *args, **kwargs):
            entry.data = data

        mock_update.side_effect = update_mock

        result = await async_migrate_entry(hass, config_entry)

        # Ensure migration was successful
        assert result is True
        # Ensure version is bumped
        assert config_entry.version == 2
        # Ensure default model is added if requested
        assert "model" in config_entry.data
        assert config_entry.data["model"] == "whisper_flex_2"
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
