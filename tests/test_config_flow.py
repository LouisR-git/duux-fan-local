from unittest.mock import patch

from custom_components.duux_fan_local.const import (
    CONF_DEVICE_ID,
    CONF_MODEL,
    CONF_USE_TLS,
)
from custom_components.duux_fan_local.config_flow import (
    DuuxFanConfigFlow,
    MqttCredentials,
    test_broker_connection as run_test_broker_connection,
    test_device_connection as run_test_device_connection,
)


async def test_step_user_success(hass):
    """Test standard config flow user step."""

    flow = DuuxFanConfigFlow()
    flow.hass = hass

    with patch(
        "custom_components.duux_fan_local.config_flow.test_broker_connection",
        return_value=True,
    ):
        result = await flow.async_step_user(
            {"username": "test", "password": "password"}
        )

        # User step should succeed and move to 'device' step
        assert result["type"] == "form"
        assert result["step_id"] == "device"


async def test_step_user_with_use_tls_false(hass):
    """Test user step with use_tls set to False and default port 443."""

    flow = DuuxFanConfigFlow()
    flow.hass = hass

    with patch(
        "custom_components.duux_fan_local.config_flow.test_broker_connection",
        return_value=True,
    ) as mock_test_broker:
        result = await flow.async_step_user(
            {
                "username": "test",
                "password": "password",
                "use_tls": False,
            }
        )

        assert result["type"] == "form"
        assert result["step_id"] == "device"
        mock_test_broker.assert_called_once_with(
            "test", "password", "collector3.cloudgarden.nl", 443, False
        )
        assert flow._use_tls is False


async def test_step_device_success(hass):
    """Test device config flow step logic with profile models."""

    flow = DuuxFanConfigFlow()
    flow.hass = hass
    # Mock context to prevent unique_id abort check failures
    flow.context = {"source": "user"}

    user_input = {
        CONF_DEVICE_ID: "AA:BB:CC:DD:EE:FF",
        "name": "My Bright 2",
        CONF_MODEL: "bright_2",
    }

    with (
        patch(
            "custom_components.duux_fan_local.config_flow.test_device_connection",
            return_value=True,
        ),
        patch(
            "homeassistant.config_entries.ConfigFlow.async_set_unique_id",
            return_value=None,
        ),
        patch(
            "homeassistant.config_entries.ConfigFlow._abort_if_unique_id_configured",
            return_value=None,
        ),
    ):
        result = await flow.async_step_device(user_input)

        # Ensure entry creation
        assert result["type"] == "create_entry"
        assert result["title"] == "My Bright 2"
        assert result["data"]["device_id"] == "aa:bb:cc:dd:ee:ff"  # Ensure lowered
        assert result["data"]["model"] == "bright_2"
        assert result["data"][CONF_USE_TLS] is True
        assert result["data"]["mqtt_port"] == 443


async def test_step_device_skips_device_check_when_no_tls(hass):
    """Test device check is skipped and entry created directly when no TLS."""

    flow = DuuxFanConfigFlow()
    flow.hass = hass
    flow.context = {"source": "user"}
    flow._use_tls = False

    user_input = {
        CONF_DEVICE_ID: "AA:BB:CC:DD:EE:FF",
        "name": "My Local Fan",
        CONF_MODEL: "whisper_flex_2",
    }

    with (
        patch(
            "custom_components.duux_fan_local.config_flow.test_device_connection"
        ) as mock_test_device,
        patch(
            "homeassistant.config_entries.ConfigFlow.async_set_unique_id",
            return_value=None,
        ),
        patch(
            "homeassistant.config_entries.ConfigFlow._abort_if_unique_id_configured",
            return_value=None,
        ),
    ):
        result = await flow.async_step_device(user_input)

        assert result["type"] == "create_entry"
        assert result["title"] == "My Local Fan"
        assert result["data"]["device_id"] == "aa:bb:cc:dd:ee:ff"
        assert result["data"]["model"] == "whisper_flex_2"
        assert result["data"][CONF_USE_TLS] is False
        assert result["data"]["mqtt_port"] == 443
        mock_test_device.assert_not_called()


def test_test_broker_connection_tls():
    """Test test_broker_connection calls tls_set without arguments when use_tls is True."""
    with patch("paho.mqtt.client.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        result = run_test_broker_connection("u", "p", "host", 443, use_tls=True)
        assert result is True
        mock_client.tls_set.assert_called_once_with()
        mock_client.connect.assert_called_once_with("host", 443, 60)
        mock_client.disconnect.assert_called_once()


def test_test_broker_connection_no_tls():
    """Test test_broker_connection skips tls_set when use_tls is False."""
    with patch("paho.mqtt.client.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        result = run_test_broker_connection("u", "p", "host", 1883, use_tls=False)
        assert result is True
        mock_client.tls_set.assert_not_called()
        mock_client.connect.assert_called_once_with("host", 1883, 60)
        mock_client.disconnect.assert_called_once()


def test_test_device_connection_tls():
    """Test test_device_connection calls tls_set without arguments when use_tls is True."""
    creds = MqttCredentials(device_id="aa:bb", use_tls=True)
    with patch("paho.mqtt.client.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value

        def fake_loop_start():
            mock_client.on_connect(mock_client, None, None, 0)
            mock_client.on_message(mock_client, None, None)

        mock_client.loop_start.side_effect = fake_loop_start

        result = run_test_device_connection(creds)
        assert result is True
        mock_client.tls_set.assert_called_once_with()


def test_test_device_connection_no_tls():
    """Test test_device_connection skips tls_set when use_tls is False."""
    creds = MqttCredentials(device_id="aa:bb", use_tls=False)
    with patch("paho.mqtt.client.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value

        def fake_loop_start():
            mock_client.on_message(mock_client, None, None)

        mock_client.loop_start.side_effect = fake_loop_start

        result = run_test_device_connection(creds)
        assert result is True
        mock_client.tls_set.assert_not_called()
