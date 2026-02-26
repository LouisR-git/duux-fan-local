"""
MQTT client manager for the Duux Fan Local integration.
Handles the connection to the custom broker and parses incoming state payloads.
"""

import json
import logging
import ssl
import asyncio

import paho.mqtt.client as mqtt
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEVICE_ID,
    CONF_MQTT_HOST,
    CONF_MQTT_PORT,
    MQTT_HOST,
    MQTT_PORT,
    TOPIC_COMMAND,
    TOPIC_STATE,
)

_LOGGER = logging.getLogger(__name__)


class DuuxMqttClient:
    """Manages a single MQTT connection for a Duux device."""

    def __init__(self, hass: HomeAssistant, config: dict):
        """Initialize the client."""
        self.hass = hass
        self.device_id = config[
            CONF_DEVICE_ID
        ].lower()  # Ensure MAC address is lowercase
        self.command_topic = TOPIC_COMMAND.format(device_id=self.device_id)
        self.state_topic = TOPIC_STATE.format(device_id=self.device_id)
        self._username = config.get(CONF_USERNAME)
        self._password = config.get(CONF_PASSWORD)
        self._mqtt_host = config.get(CONF_MQTT_HOST, MQTT_HOST)
        self._mqtt_port = config.get(CONF_MQTT_PORT, MQTT_PORT)
        self._callbacks = []
        self._client = mqtt.Client()
        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message

    async def async_connect(self):
        """Asynchronously configure TLS and connect to the MQTT broker."""
        loop = asyncio.get_running_loop()

        def configure_tls_and_connect():
            if self._username:
                self._client.username_pw_set(self._username, self._password)
            self._client.tls_set(cert_reqs=ssl.CERT_NONE)
            self._client.connect(self._mqtt_host, self._mqtt_port, 60)

        try:
            await loop.run_in_executor(None, configure_tls_and_connect)
            self._client.loop_start()
        except (OSError, ConnectionRefusedError) as err:
            _LOGGER.error("Failed to connect to Duux MQTT broker: %s", err)

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        self._client.loop_stop()
        self._client.disconnect()

    def publish(self, payload: str):
        """Publish a message to the command topic."""
        self._client.publish(self.command_topic, payload, qos=0, retain=False)
        _LOGGER.debug("Published to %s: %s", self.command_topic, payload)

    def on_connect(self, client, userdata, flags, rc):
        """Handle connection to the broker."""
        if rc == 0:
            _LOGGER.info("Connected to Duux MQTT broker for device %s", self.device_id)
            self._client.subscribe(self.state_topic, qos=1)
            _LOGGER.info("Subscribed to state topic: %s", self.state_topic)
        else:
            _LOGGER.error("Failed to connect to Duux MQTT, return code %d", rc)

    def on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages from the paho-mqtt thread."""
        try:
            data = json.loads(msg.payload)
            _LOGGER.debug("Received message on %s: %s", msg.topic, data)
            fan_data = data.get("sub", {}).get("Tune", [{}])[0]

            # Some models like Bright 2 nest the payload again under "sub"
            if (
                isinstance(fan_data, dict)
                and "sub" in fan_data
                and "Tune" in fan_data["sub"]
            ):
                fan_data = fan_data["sub"]["Tune"][0]

            if isinstance(fan_data, dict) and fan_data:
                for update_callback in self._callbacks:
                    self.hass.add_job(update_callback, fan_data)
            else:
                _LOGGER.debug(
                    "Parsed fan_data is empty or not a dict. Skipping update."
                )
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            _LOGGER.warning(
                "Could not parse payload on %s: %s (Error: %s)",
                msg.topic,
                msg.payload,
                e,
            )

    def register_callback(self, update_callback):
        """Register a callback to be called on new messages."""
        self._callbacks.append(update_callback)

    def unregister_callback(self, update_callback):
        """Unregister a callback."""
        if update_callback in self._callbacks:
            self._callbacks.remove(update_callback)
