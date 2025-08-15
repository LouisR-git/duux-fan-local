"""Config flow for Duux Fan."""
from __future__ import annotations
import logging
import ssl
import threading
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_MODEL,
    CONF_PASSWORD,
    CONF_USERNAME,
    MODELS,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_TIMEOUT,
    TOPIC_STATE,
)

_LOGGER = logging.getLogger(__name__)

def test_connection(
    device_id: str, username: str | None = None, password: str | None = None
) -> bool:
    """Tests the connection to the Duux MQTT broker by listening for a message."""
    import paho.mqtt.client as mqtt

    connection_event = threading.Event()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(TOPIC_STATE.format(device_id=device_id))
        else:
            connection_event.set()

    def on_message(client, userdata, msg):
        connection_event.set()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    if username or password:
        client.username_pw_set(username, password)

    client.tls_set(cert_reqs=ssl.CERT_NONE)

    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_start()
        connected = connection_event.wait(timeout=MQTT_TIMEOUT)
        client.loop_stop()
        client.disconnect()
        return connected
    except (OSError, ConnectionRefusedError) as e:
        _LOGGER.error("MQTT connection error: %s", e)
        return False
    except Exception as e:
        if isinstance(e, ImportError):
            _LOGGER.error("paho-mqtt library not found. Please ensure it's in requirements.")
        else:
            _LOGGER.error("An unexpected error occurred during connection test: %s", e)
        return False


class DuuxFanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Duux Fan."""

    VERSION = 1
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Redirect to the connection step."""
        return await self.async_step_connection(user_input)

    async def async_step_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose between anonymous or credentialed connection."""
        if user_input is not None:
            if user_input["connection_type"] == "credentials":
                return await self.async_step_credentials()
            self._data = {}
            return await self.async_step_device()

        data_schema = vol.Schema(
            {
                vol.Required("connection_type", default="anonymous"): vol.In(
                    {
                        "anonymous": "Anonymous",
                        "credentials": "Username and password",
                    }
                )
            }
        )

        return self.async_show_form(step_id="connection", data_schema=data_schema)

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Collect MQTT credentials."""
        if user_input is not None:
            self._data[CONF_USERNAME] = user_input[CONF_USERNAME]
            self._data[CONF_PASSWORD] = user_input[CONF_PASSWORD]
            return await self.async_step_device()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(step_id="credentials", data_schema=data_schema)

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure fan details and test connection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_DEVICE_ID] = user_input[CONF_DEVICE_ID].lower()

            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            is_connected = await self.hass.async_add_executor_job(
                test_connection,
                user_input[CONF_DEVICE_ID],
                self._data.get(CONF_USERNAME),
                self._data.get(CONF_PASSWORD),
            )

            if is_connected:
                self._data.update(
                    {
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
                        CONF_MODEL: user_input[CONF_MODEL],
                    }
                )
                return self.async_create_entry(
                    title=self._data[CONF_NAME], data=self._data
                )

            errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_DEVICE_ID): str,
                vol.Required(CONF_MODEL): vol.In(MODELS),
            }
        )

        return self.async_show_form(
            step_id="device", data_schema=data_schema, errors=errors
        )
