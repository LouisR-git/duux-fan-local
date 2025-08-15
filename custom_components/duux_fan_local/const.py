DOMAIN = "duux_fan_local"

# Configuration keys
CONF_DEVICE_ID = "device_id"
CONF_MODEL = "model"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
MANUFACTURER = "Duux"
MODELS = {
    "whisper_flex_1": "Whisper Flex 1",
    "whisper_flex_2": "Whisper Flex 2",
}

# Model versions
MODEL_V1 = "whisper_flex_1"
MODEL_V2 = "whisper_flex_2"

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
# V1 specific oscillation attributes
ATTR_SWING = "swing"
ATTR_TILT = "tilt"
ATTR_NIGHT_MODE = "night"
ATTR_CHILD_LOCK = "lock"
ATTR_BATCHA = "batcha"
ATTR_BATLVL = "batlvl"

# Min/Max values
MAX_VER_OSC = 2
MAX_HOR_OSC = 3
MAX_SPEED_V1 = 26
MAX_SPEED_V2 = 30
MAX_TIMER = 12

# V1 specific mode mapping
V1_MODE_OPTIONS = {
    "Normal": 0,
    "Natural": 1,
    "Night": 2,
}

# V2 specific mode mapping
V2_MODE_OPTIONS = {
    "Fan": 0,
    "Natural": 1,
}

# V1 oscillation options (binary on/off)
V1_HOR_OSC_OPTIONS = {
    "Off": 0,
    "On": 1,
}

V1_VER_OSC_OPTIONS = {
    "Off": 0,
    "On": 1,
}

# V2 oscillation options (varying angles)
V2_HOR_OSC_OPTIONS = {
    "Off": 0,
    "30°": 1,
    "60°": 2,
    "90°": 3,
}

V2_VER_OSC_OPTIONS = {
    "Off": 0,
    "45°": 1,
    "100°": 2,
}