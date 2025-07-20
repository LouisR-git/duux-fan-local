import json
import logging
import ssl
import asyncio

import paho.mqtt.client as mqtt
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEVICE_ID,
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
        self.device_id = config[CONF_DEVICE_ID]
        self.command_topic = TOPIC_COMMAND.format(device_id=self.device_id)
        self.state_topic = TOPIC_STATE.format(device_id=self.device_id)
        self._callbacks = []
        self._client = mqtt.Client()
        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message
        
        self._client.tls_set(cert_reqs=ssl.CERT_NONE)

    def connect(self):
        """Connect to the MQTT broker."""
        try:
            self._client.connect(MQTT_HOST, MQTT_PORT, 60)
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

            # Check if parsing resulted in a valid, non-empty dictionary
            if isinstance(fan_data, dict) and fan_data:
                for update_callback in self._callbacks:
                    self.hass.add_job(update_callback, fan_data)
            else:
                _LOGGER.debug("Parsed fan_data is empty or not a dict. Skipping update.")

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            _LOGGER.warning("Could not parse payload on %s: %s (Error: %s)", msg.topic, msg.payload, e)

    def register_callback(self, update_callback):
        """Register a callback to be called on new messages."""
        self._callbacks.append(update_callback)

    def unregister_callback(self, update_callback):
        """Unregister a callback."""
        if update_callback in self._callbacks:
            self._callbacks.remove(update_callback)