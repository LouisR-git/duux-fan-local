from .devices import DEVICE_PROFILES

DOMAIN = "duux_fan_local"

# Configuration keys
CONF_DEVICE_ID = "device_id"
CONF_MODEL = "model"
CONF_MQTT_HOST = "mqtt_host"
CONF_MQTT_PORT = "mqtt_port"
MANUFACTURER = "Duux"

# Generate MODELS dynamically from DEVICE_PROFILES
MODELS = {key: profile["name"] for key, profile in DEVICE_PROFILES.items()}

# MQTT Details
MQTT_HOST = "collector3.cloudgarden.nl"
MQTT_PORT = 443
MQTT_TIMEOUT = 10

# Topics
TOPIC_COMMAND = "sensor/{device_id}/command"
TOPIC_STATE = "sensor/{device_id}/in"