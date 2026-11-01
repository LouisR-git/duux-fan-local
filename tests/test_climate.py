"""Unit tests for the Duux heater (climate) platform."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.climate import HVACMode
from homeassistant.const import ATTR_TEMPERATURE

from custom_components.duux_fan_local.climate import (
    DuuxHeater,
    async_setup_entry,
)
from custom_components.duux_fan_local.const import DOMAIN
from custom_components.duux_fan_local.devices import DEVICE_PROFILES


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.publish = MagicMock()
    client.register_callback = MagicMock()
    client.unregister_callback = MagicMock()
    return client


def _make_heater(mock_client, name="Heater"):
    return DuuxHeater(
        client=mock_client,
        device_id="aa:bb:cc:dd:ee:ff",
        base_name=name,
        model="edge_2000",
        details=DEVICE_PROFILES["edge_2000"]["climate"],
    )


def test_heater_init(mock_client):
    """Test heater entity properties and initialization."""
    heater = _make_heater(mock_client, name="Playroom Heater")

    assert heater.name == "Playroom Heater"
    assert heater.unique_id == f"{DOMAIN}_aa:bb:cc:dd:ee:ff_climate"
    assert heater.hvac_modes == [HVACMode.OFF, HVACMode.HEAT]
    assert heater.hvac_mode == HVACMode.OFF
    assert heater.min_temp == 5.0
    assert heater.max_temp == 36.0
    assert heater.target_temperature_step == 1.0
    assert heater.target_temperature is None
    assert heater.current_temperature is None


async def test_heater_turn_on_off(hass, mock_client):
    """Test turn on and turn off methods publish correct MQTT payloads."""
    heater = _make_heater(mock_client)
    heater.hass = hass

    await heater.async_turn_on()
    mock_client.publish.assert_called_with("tune set power 1")

    await heater.async_turn_off()
    mock_client.publish.assert_called_with("tune set power 0")


async def test_heater_set_hvac_mode(hass, mock_client):
    """Test HVAC modes map to power commands."""
    heater = _make_heater(mock_client)
    heater.hass = hass

    await heater.async_set_hvac_mode(HVACMode.HEAT)
    mock_client.publish.assert_called_with("tune set power 1")

    await heater.async_set_hvac_mode(HVACMode.OFF)
    mock_client.publish.assert_called_with("tune set power 0")

    mock_client.publish.reset_mock()
    await heater.async_set_hvac_mode(HVACMode.COOL)
    mock_client.publish.assert_not_called()


async def test_heater_set_temperature(hass, mock_client):
    """Test setting target temperature respects step and min/max limits."""
    heater = _make_heater(mock_client)
    heater.hass = hass

    await heater.async_set_temperature(**{ATTR_TEMPERATURE: 21})
    mock_client.publish.assert_called_with("tune set sp 21")

    # Test stepping: 20.6 rounds to 21
    await heater.async_set_temperature(**{ATTR_TEMPERATURE: 20.6})
    mock_client.publish.assert_called_with("tune set sp 21")

    # Test clamping minimum: 2 clamps to min 5
    await heater.async_set_temperature(**{ATTR_TEMPERATURE: 2})
    mock_client.publish.assert_called_with("tune set sp 5")

    # Test clamping maximum: 40 clamps to max 36
    await heater.async_set_temperature(**{ATTR_TEMPERATURE: 40})
    mock_client.publish.assert_called_with("tune set sp 36")

    # No temperature given: nothing is published
    mock_client.publish.reset_mock()
    await heater.async_set_temperature()
    mock_client.publish.assert_not_called()


def test_heater_update_state(mock_client):
    """Test updating state from an Edge 2000 MQTT payload."""
    heater = _make_heater(mock_client)
    heater.async_write_ha_state = MagicMock()

    payload = {
        "uid": "oryf2o5f8wmaeaav",
        "id": 1,
        "power": 1,
        "sp": 18,
        "temp": 14,
        "mode": 0,
        "lock": 0,
        "status": 0,
        "timer": 0,
        "timRm": 0,
        "err": 1,
        "night": 0,
        "eco": 2,
    }
    heater._update_state(payload)

    assert heater.hvac_mode == HVACMode.HEAT
    assert heater.target_temperature == 18.0
    assert heater.current_temperature == 14.0
    heater.async_write_ha_state.assert_called_once()

    heater._update_state({"power": 0})
    assert heater.hvac_mode == HVACMode.OFF
    assert heater.target_temperature == 18.0


async def test_async_setup_entry_with_climate(hass, mock_client):
    """Test async_setup_entry adds entity when profile supports climate."""
    config_entry = MagicMock()
    config_entry.entry_id = "test_entry"
    config_entry.data = {
        "device_id": "aa:bb:cc:dd:ee:ff",
        "name": "Edge Heater",
        "model": "edge_2000",
    }
    hass.data = {DOMAIN: {"test_entry": mock_client}}

    entities_added = []
    async_add_entities = MagicMock(
        side_effect=lambda entities: entities_added.extend(entities)
    )

    await async_setup_entry(hass, config_entry, async_add_entities)

    assert len(entities_added) == 1
    assert isinstance(entities_added[0], DuuxHeater)


async def test_async_setup_entry_without_climate(hass, mock_client):
    """Test async_setup_entry skips adding entity when model has no climate."""
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
