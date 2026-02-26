"""
Configuration flow for Duux Fan Local.
Handles UI setup, discovering devices, and testing the MQTT connection.
"""

from __future__ import annotations
import logging
import ssl
import threading
from dataclasses import dataclass
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_MODEL,
    CONF_MQTT_HOST,
    CONF_MQTT_PORT,
    MODELS,
    MQTT_HOST,
    MQTT_PORT,
    MQTT_TIMEOUT,
    TOPIC_STATE,
)

_LOGGER = logging.getLogger(__name__)


def test_broker_connection(
    username: str | None, password: str | None, host: str, port: int
) -> bool:
    """Test connection to the MQTT broker."""
    import paho.mqtt.client as mqtt

    client = mqtt.Client()
    if username:
        client.username_pw_set(username, password)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    try:
        client.connect(host, port, 60)
        client.disconnect()
        return True
    except (OSError, ConnectionRefusedError) as e:
        _LOGGER.error("MQTT connection error: %s", e)
        return False
    except Exception as e:
        if isinstance(e, ImportError):
            _LOGGER.error(
                "paho-mqtt library not found. Please ensure it's in requirements."
            )
        else:
            _LOGGER.error("An unexpected error occurred during connection test: %s", e)
        return False


@dataclass
class MqttCredentials:
    """MQTT connection credentials."""

    device_id: str
    username: str | None = None
    password: str | None = None
    host: str = MQTT_HOST
    port: int = MQTT_PORT


def test_device_connection(credentials: MqttCredentials) -> bool:
    """Tests the connection to the Duux MQTT broker by listening for a message."""
    import paho.mqtt.client as mqtt

    connection_event = threading.Event()

    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(TOPIC_STATE.format(device_id=credentials.device_id))
        else:
            connection_event.set()

    def on_message(client, userdata, msg):
        connection_event.set()

    client = mqtt.Client()
    if credentials.username:
        client.username_pw_set(credentials.username, credentials.password)
    client.on_connect = on_connect
    client.on_message = on_message

    client.tls_set(cert_reqs=ssl.CERT_NONE)

    try:
        client.connect(credentials.host, credentials.port, 60)
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
            _LOGGER.error(
                "paho-mqtt library not found. Please ensure it's in requirements."
            )
        else:
            _LOGGER.error("An unexpected error occurred during connection test: %s", e)
        return False


class DuuxFanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Duux Fan."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._username: str | None = None
        self._password: str | None = None
        self._mqtt_host: str = MQTT_HOST
        self._mqtt_port: int = MQTT_PORT

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the first step of the flow: MQTT credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._username = user_input.get(CONF_USERNAME)
            self._password = user_input.get(CONF_PASSWORD)
            self._mqtt_host = user_input.get(CONF_MQTT_HOST, MQTT_HOST)
            self._mqtt_port = user_input.get(CONF_MQTT_PORT, MQTT_PORT)

            is_connected = await self.hass.async_add_executor_job(
                test_broker_connection,
                self._username,
                self._password,
                self._mqtt_host,
                self._mqtt_port,
            )

            if is_connected:
                return await self.async_step_device()

            errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_USERNAME): str,
                vol.Optional(CONF_PASSWORD): str,
                vol.Optional(CONF_MQTT_HOST, default=MQTT_HOST): str,
                vol.Optional(CONF_MQTT_PORT, default=MQTT_PORT): int,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the second step of the flow: device details."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_DEVICE_ID] = user_input[CONF_DEVICE_ID].lower()

            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            credentials = MqttCredentials(
                device_id=user_input[CONF_DEVICE_ID],
                username=self._username,
                password=self._password,
                host=self._mqtt_host,
                port=self._mqtt_port,
            )

            is_connected = await self.hass.async_add_executor_job(
                test_device_connection,
                credentials,
            )

            if is_connected:
                return self._create_device_entry(user_input)

            errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_MODEL): vol.In(MODELS),
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_DEVICE_ID): str,
            }
        )

        return self.async_show_form(
            step_id="device", data_schema=data_schema, errors=errors
        )

    def _create_device_entry(self, user_input: dict[str, Any]) -> FlowResult:
        """Create the config entry after a successful connection."""
        data = {
            CONF_MODEL: user_input[CONF_MODEL],
            CONF_NAME: user_input[CONF_NAME],
            CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
            CONF_MQTT_HOST: self._mqtt_host,
            CONF_MQTT_PORT: self._mqtt_port,
        }
        if self._username:
            data[CONF_USERNAME] = self._username
        if self._password:
            data[CONF_PASSWORD] = self._password
        return self.async_create_entry(title=user_input[CONF_NAME], data=data)
