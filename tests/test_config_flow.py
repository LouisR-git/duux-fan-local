from unittest.mock import patch

from custom_components.duux_fan_local.const import CONF_DEVICE_ID, CONF_MODEL
from custom_components.duux_fan_local.config_flow import DuuxFanConfigFlow


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
