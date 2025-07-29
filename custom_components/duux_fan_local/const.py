DOMAIN = "duux_fan_local"

# Configuration keys
CONF_DEVICE_ID = "device_id"
CONF_MODEL = "model"
MANUFACTURER = "Duux"
MODELS = {
    "whisper_flex_2": "Whisper Flex 2",
}

# MQTT Details
MQTT_HOST = "collector3.cloudgarden.nl"
MQTT_PORT = 443
MQTT_TIMEOUT = 10

# Topics
TOPIC_COMMAND = "sensor/{device_id}/command"
TOPIC_STATE = "sensor/{device_id}/in"

# Fan attributes from payload
ATTR_POWER = "power"
ATTR_SPEED = "speed"
ATTR_MODE = "mode"
ATTR_TIMER = "timer"
ATTR_HOR_OSC = "horosc"
ATTR_VER_OSC = "verosc"
ATTR_NIGHT_MODE = "night"
ATTR_CHILD_LOCK = "lock"
ATTR_BATCHA = "batcha"
ATTR_BATLVL = "batlvl"

# Min/Max values
MAX_VER_OSC = 2
MAX_HOR_OSC = 3
MAX_SPEED = 30
MAX_TIMER = 12