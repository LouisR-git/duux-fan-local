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

from .const import DOMAIN, CONF_DEVICE_ID, CONF_MODEL, MODELS, MQTT_HOST, MQTT_PORT, MQTT_TIMEOUT, TOPIC_STATE

_LOGGER = logging.getLogger(__name__)

def test_connection(device_id: str) -> bool:
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


    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            is_connected = await self.hass.async_add_executor_job(
                test_connection, user_input[CONF_DEVICE_ID]
            )

            if is_connected:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )
            
            errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_MODEL): vol.In(MODELS),
                vol.Required(CONF_NAME, default="Living Room Fan"): str,
                vol.Required(CONF_DEVICE_ID): str,
                
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
