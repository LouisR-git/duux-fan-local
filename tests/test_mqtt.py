import json
import logging
from unittest.mock import Mock, patch
from homeassistant.core import HomeAssistant

from custom_components.duux_fan_local.mqtt import DuuxMqttClient
from custom_components.duux_fan_local.const import CONF_DEVICE_ID


def test_mqtt_client_initialization(hass: HomeAssistant):
    """Test that the client initializes correctly with config data."""
    config = {
        CONF_DEVICE_ID: "AA:BB:CC:DD:EE:FF",
        "username": "testuser",
        "password": "testpassword",
    }
    client = DuuxMqttClient(hass, config)
    assert client.device_id == "aa:bb:cc:dd:ee:ff"
    assert client.command_topic == "sensor/aa:bb:cc:dd:ee:ff/command"
    assert client.state_topic == "sensor/aa:bb:cc:dd:ee:ff/in"


def test_on_message_standard_payload(hass: HomeAssistant):
    """Test parsing a standard single-nested payload (like Whisper Flex)."""
    client = DuuxMqttClient(hass, {CONF_DEVICE_ID: "test_mac"})
    mock_callback = Mock()
    client.register_callback(mock_callback)

    # Simulate standard payload
    payload = {"sub": {"Tune": [{"power": 1, "speed": 10, "mode": 2}]}}

    mock_msg = Mock()
    mock_msg.topic = client.state_topic
    mock_msg.payload = json.dumps(payload)

    with patch.object(hass, "add_job") as mock_add_job:
        client.on_message(None, None, mock_msg)

        # Verify the callback was triggered via add_job
        mock_add_job.assert_called_once_with(
            mock_callback, {"power": 1, "speed": 10, "mode": 2}
        )


def test_on_message_double_nested_payload(hass: HomeAssistant):
    """Test parsing a double-nested payload (like Duux Bright 2)."""
    client = DuuxMqttClient(hass, {CONF_DEVICE_ID: "test_mac"})
    mock_callback = Mock()
    client.register_callback(mock_callback)

    # Simulate double nested payload
    payload = {
        "sub": {
            "Tune": [
                {
                    "uid": "123456",
                    "rssi": -46,
                    "sub": {
                        "Tune": [{"power": 1, "ppm": 17, "speed": 0, "filter": 51}]
                    },
                }
            ]
        }
    }

    mock_msg = Mock()
    mock_msg.topic = client.state_topic
    mock_msg.payload = json.dumps(payload)

    with patch.object(hass, "add_job") as mock_add_job:
        client.on_message(None, None, mock_msg)

        # Verify the callback was triggered with the *inner* dictionary payload
        mock_add_job.assert_called_once_with(
            mock_callback, {"power": 1, "ppm": 17, "speed": 0, "filter": 51}
        )


def test_on_message_invalid_payload(hass: HomeAssistant, caplog):
    """Test handling of invalid JSON payloads."""
    client = DuuxMqttClient(hass, {CONF_DEVICE_ID: "test_mac"})
    mock_callback = Mock()
    client.register_callback(mock_callback)

    mock_msg = Mock()
    mock_msg.topic = client.state_topic
    mock_msg.payload = "this is not valid json"

    with caplog.at_level(logging.WARNING):
        client.on_message(None, None, mock_msg)
        assert "Could not parse payload" in caplog.text

    # Ensure no callbacks were registered
    assert mock_callback.call_count == 0
