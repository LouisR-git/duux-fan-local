"""Unit tests for the Duux dehumidifier platform."""
from unittest.mock import MagicMock

import pytest
from homeassistant.components.humidifier import HumidifierDeviceClass

from custom_components.duux_fan_local.const import DOMAIN
from custom_components.duux_fan_local.devices import DEVICE_PROFILES
from custom_components.duux_fan_local.humidifier import (
    DuuxDehumidifier,
    async_setup_entry,
)


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.publish = MagicMock()
    client.register_callback = MagicMock()
    client.unregister_callback = MagicMock()
    return client


def test_dehumidifier_init(mock_client):
    """Test dehumidifier entity properties and initialization."""
    profile = DEVICE_PROFILES["bora_smart"]
    details = profile["humidifier"]

    dehumidifier = DuuxDehumidifier(
        client=mock_client,
        device_id="aa:bb:cc:dd:ee:ff",
        base_name="Living Room Dehumidifier",
        model="bora_smart",
        details=details,
    )

    assert dehumidifier.name == "Living Room Dehumidifier"
    assert dehumidifier.unique_id == f"{DOMAIN}_aa:bb:cc:dd:ee:ff_humidifier"
    assert dehumidifier.device_class == HumidifierDeviceClass.DEHUMIDIFIER
    assert dehumidifier.min_humidity == 30.0
    assert dehumidifier.max_humidity == 80.0
    assert dehumidifier.is_on is False
    assert dehumidifier.target_humidity is None
    assert dehumidifier.current_humidity is None


async def test_dehumidifier_turn_on_off(hass, mock_client):
    """Test turn on and turn off methods publish correct MQTT payloads."""
    profile = DEVICE_PROFILES["bora_smart"]
    details = profile["humidifier"]

    dehumidifier = DuuxDehumidifier(
        client=mock_client,
        device_id="aa:bb:cc:dd:ee:ff",
        base_name="Dehumidifier",
        model="bora_smart",
        details=details,
    )
    dehumidifier.hass = hass

    await dehumidifier.async_turn_on()
    mock_client.publish.assert_called_with("tune set power 1")

    await dehumidifier.async_turn_off()
    mock_client.publish.assert_called_with("tune set power 0")


async def test_dehumidifier_set_humidity(hass, mock_client):
    """Test setting target humidity respects step and min/max limits."""
    profile = DEVICE_PROFILES["bora_smart"]
    details = profile["humidifier"]

    dehumidifier = DuuxDehumidifier(
        client=mock_client,
        device_id="aa:bb:cc:dd:ee:ff",
        base_name="Dehumidifier",
        model="bora_smart",
        details=details,
    )
    dehumidifier.hass = hass

    # Test stepping: 47 rounds to 45
    await dehumidifier.async_set_humidity(47)
    mock_client.publish.assert_called_with("tune set sp 45")

    # Test clamping minimum: 20 clamps to min 30
    await dehumidifier.async_set_humidity(20)
    mock_client.publish.assert_called_with("tune set sp 30")

    # Test clamping maximum: 95 clamps to max 80
    await dehumidifier.async_set_humidity(95)
    mock_client.publish.assert_called_with("tune set sp 80")


def test_dehumidifier_update_state(mock_client):
    """Test updating state from MQTT device payload."""
    profile = DEVICE_PROFILES["bora_smart"]
    details = profile["humidifier"]

    dehumidifier = DuuxDehumidifier(
        client=mock_client,
        device_id="aa:bb:cc:dd:ee:ff",
        base_name="Dehumidifier",
        model="bora_smart",
        details=details,
    )
    dehumidifier.async_write_ha_state = MagicMock()

    payload = {"power": 1, "sp": 50, "hum": 62}
    dehumidifier._update_state(payload)

    assert dehumidifier.is_on is True
    assert dehumidifier.target_humidity == 50
    assert dehumidifier.current_humidity == 62.0
    dehumidifier.async_write_ha_state.assert_called_once()


async def test_async_setup_entry_with_humidifier(hass, mock_client):
    """Test async_setup_entry adds entity when profile supports humidifier."""
    config_entry = MagicMock()
    config_entry.entry_id = "test_entry"
    config_entry.data = {
        "device_id": "aa:bb:cc:dd:ee:ff",
        "name": "Bora Dehumidifier",
        "model": "bora_smart",
    }
    hass.data = {DOMAIN: {"test_entry": mock_client}}

    entities_added = []
    async_add_entities = MagicMock(
        side_effect=lambda entities: entities_added.extend(entities)
    )

    await async_setup_entry(hass, config_entry, async_add_entities)

    assert len(entities_added) == 1
    assert isinstance(entities_added[0], DuuxDehumidifier)


async def test_async_setup_entry_without_humidifier(hass, mock_client):
    """Test async_setup_entry skips adding entity when model has no humidifier."""
    config_entry = MagicMock()
    config_entry.entry_id = "test_entry"
    config_entry.data = {
        "device_id": "aa:bb:cc:dd:ee:ff",
        "name": "Fan",
        "model": "whisper_flex_2",
    }
    hass.data = {DOMAIN: {"test_entry": mock_client}}

    async_add_entities = MagicMock()

    await async_setup_entry(hass, config_entry, async_add_entities)

    async_add_entities.assert_not_called()
