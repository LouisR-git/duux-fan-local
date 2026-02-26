"""
Device Profiles for Duux products.
This module defines the schema and configurations for various Duux models
(fans, air purifiers, etc.), mapping their MQTT payloads to Home Assistant entities.
"""

import voluptuous as vol
import logging

_LOGGER = logging.getLogger(__name__)

# Common attributes
ATTR_POWER = "power"
ATTR_SPEED = "speed"
ATTR_MODE = "mode"
ATTR_TIMER = "timer"
ATTR_NIGHT_MODE = "night"
ATTR_CHILD_LOCK = "lock"
ATTR_BATLVL = "batlvl"
ATTR_BATCHA = "batcha"
# Fan attributes
ATTR_HOR_OSC = "horosc"
ATTR_VER_OSC = "verosc"
ATTR_SWING = "swing"
ATTR_TILT = "tilt"
# Air purifier attributes
ATTR_FILTER = "filter"
ATTR_PPM = "ppm"
ATTR_ION = "ion"
ATTR_AQ = "AQ"
ATTR_TVOC = "TVOC"

# Schema validation for device profiles
# This ensures any new models added in the future strictly adhere to the expected format.
DEVICE_PROFILE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,
        vol.Optional("fan"): vol.Schema(
            {
                vol.Optional("supported_features"): [str],
                vol.Optional("max_speed"): int,
                vol.Optional("power_key"): str,
                vol.Optional("speed_key"): str,
            }
        ),
        vol.Optional("switches"): vol.Schema(
            {
                vol.Extra: vol.Schema(
                    {
                        vol.Required("name"): str,
                        vol.Required("command_on"): str,
                        vol.Required("command_off"): str,
                        vol.Required("state_key"): str,
                        vol.Optional("icon"): vol.Any(str, None),
                        vol.Optional("entity_category"): vol.Any(str, None),
                    }
                )
            }
        ),
        vol.Optional("sensors"): vol.Schema(
            {
                vol.Extra: vol.Schema(
                    {
                        vol.Required("name"): str,
                        vol.Required("state_key"): str,
                        vol.Optional("device_class"): vol.Any(str, None),
                        vol.Optional("state_class"): vol.Any(str, None),
                        vol.Optional("unit"): vol.Any(str, None),
                        vol.Optional("icon"): vol.Any(str, None),
                        vol.Optional("multiplier"): vol.Any(int, float),
                    }
                )
            }
        ),
        vol.Optional("numbers"): vol.Schema(
            {
                vol.Extra: vol.Schema(
                    {
                        vol.Required("name"): str,
                        vol.Required("command_topic"): str,
                        vol.Required("state_key"): str,
                        vol.Optional("min"): vol.Any(int, float),
                        vol.Optional("max"): vol.Any(int, float),
                        vol.Optional("step"): vol.Any(int, float),
                        vol.Optional("unit"): vol.Any(str, None),
                        vol.Optional("icon"): vol.Any(str, None),
                    }
                )
            }
        ),
        vol.Optional("select"): vol.Schema(
            {
                vol.Extra: vol.Schema(
                    {
                        vol.Required("name"): str,
                        vol.Required("command_topic"): str,
                        vol.Required("state_key"): str,
                        vol.Required("options"): dict,
                        vol.Optional("icon"): vol.Any(str, None),
                    }
                )
            }
        ),
        vol.Optional("binary_sensors"): vol.Schema(
            {
                vol.Extra: vol.Schema(
                    {
                        vol.Required("name"): str,
                        vol.Required("state_key"): str,
                        vol.Optional("device_class"): vol.Any(str, None),
                        vol.Optional("icon"): vol.Any(str, None),
                    }
                )
            }
        ),
    }
)

DEVICE_PROFILES = {
    "whisper_flex_1": {
        "name": "Whisper Flex 1",
        "fan": {
            "supported_features": [
                "turn_on",
                "turn_off",
                "set_speed",
                "oscillate",
                "direction",
            ],
            "max_speed": 26,
        },
        "switches": {
            "horizontal_oscillation_v1": {
                "name": "Horizontal Oscillation",
                "command_on": "tune set swing 1",
                "command_off": "tune set swing 0",
                "state_key": ATTR_SWING,
                "icon": "mdi:arrow-left-right",
                "entity_category": None,
            },
            "vertical_oscillation_v1": {
                "name": "Vertical Oscillation",
                "command_on": "tune set tilt 1",
                "command_off": "tune set tilt 0",
                "state_key": ATTR_TILT,
                "icon": "mdi:arrow-up-down",
                "entity_category": None,
            },
        },
        "sensors": {},
        "numbers": {
            "timer": {
                "name": "Timer",
                "command_topic": "tune set timer",
                "state_key": ATTR_TIMER,
                "min": 0.0,
                "max": 12.0,
                "step": 1.0,
                "unit": "h",
                "icon": "mdi:timer-outline",
            },
            "speed": {
                "name": "Speed",
                "command_topic": "tune set speed",
                "state_key": ATTR_SPEED,
                "min": 1.0,
                "max": 26.0,
                "step": 1.0,
                "unit": None,
                "icon": "mdi:speedometer",
            },
        },
        "select": {
            "fan_mode": {
                "name": "Fan Mode",
                "command_topic": "tune set mode",
                "state_key": ATTR_MODE,
                "options": {"Normal": 0, "Natural": 1, "Night": 2},
                "icon": "mdi:weather-windy",
            }
        },
        "binary_sensors": {},
    },
    "whisper_flex_2": {
        "name": "Whisper Flex 2",
        "fan": {
            "supported_features": ["turn_on", "turn_off", "set_speed"],
            "max_speed": 30,
        },
        "switches": {
            "night_mode": {
                "name": "Night Mode",
                "command_on": "tune set night 1",
                "command_off": "tune set night 0",
                "state_key": ATTR_NIGHT_MODE,
                "icon": "mdi:weather-night",
                "entity_category": None,
            },
            "child_lock": {
                "name": "Child Lock",
                "command_on": "tune set lock 1",
                "command_off": "tune set lock 0",
                "state_key": ATTR_CHILD_LOCK,
                "icon": "mdi:account-lock",
                "entity_category": None,
            },
        },
        "sensors": {
            "battery_level": {
                "name": "Battery Level",
                "state_key": ATTR_BATLVL,
                "device_class": "battery",
                "state_class": "measurement",
                "unit": "%",
                "icon": "mdi:battery",
                "multiplier": 10,
            }
        },
        "numbers": {
            "timer": {
                "name": "Timer",
                "command_topic": "tune set timer",
                "state_key": ATTR_TIMER,
                "min": 0.0,
                "max": 12.0,
                "step": 1.0,
                "unit": "h",
                "icon": "mdi:timer-outline",
            },
            "speed": {
                "name": "Speed",
                "command_topic": "tune set speed",
                "state_key": ATTR_SPEED,
                "min": 1.0,
                "max": 30.0,
                "step": 1.0,
                "unit": None,
                "icon": "mdi:speedometer",
            },
        },
        "select": {
            "fan_mode": {
                "name": "Fan Mode",
                "command_topic": "tune set mode",
                "state_key": ATTR_MODE,
                "options": {"Fan": 0, "Natural": 1},
                "icon": "mdi:weather-windy",
            },
            "horizontal_oscillation": {
                "name": "Horizontal Oscillation",
                "command_topic": "tune set horosc",
                "state_key": ATTR_HOR_OSC,
                "options": {"Off": 0, "30°": 1, "60°": 2, "90°": 3},
                "icon": "mdi:arrow-left-right",
            },
            "vertical_oscillation": {
                "name": "Vertical Oscillation",
                "command_topic": "tune set verosc",
                "state_key": ATTR_VER_OSC,
                "options": {"Off": 0, "45°": 1, "100°": 2},
                "icon": "mdi:arrow-up-down",
            },
        },
        "binary_sensors": {
            "charging": {
                "name": "Charging",
                "state_key": ATTR_BATCHA,
                "device_class": "battery_charging",
                "icon": "mdi:battery-charging",
            }
        },
    },
    "bright_2": {
        "name": "Duux Bright 2",
        "fan": {
            "supported_features": ["turn_on", "turn_off", "set_speed"],
            "max_speed": 4,  # 0 to 4 (0 is auto)
        },
        "switches": {
            "night_mode": {
                "name": "Night Mode",
                "command_on": "tune set mode 1",
                "command_off": "tune set mode 0",
                "state_key": ATTR_NIGHT_MODE,
                "icon": "mdi:weather-night",
                "entity_category": None,
            },
            "ion": {
                "name": "ION Setting",
                "command_on": "tune set ion 1",
                "command_off": "tune set ion 0",
                "state_key": ATTR_ION,
                "icon": "mdi:blur",
                "entity_category": None,
            },
        },
        "sensors": {
            "filter_life": {
                "name": "Filter Life",
                "state_key": ATTR_FILTER,
                "device_class": None,
                "state_class": "measurement",
                "unit": "%",
                "icon": "mdi:air-filter",
                "multiplier": 1,
            },
            "pm_10": {
                "name": "PM10",
                "state_key": ATTR_PPM,
                "device_class": "pm10",
                "state_class": "measurement",
                "unit": "µg/m³",
                "icon": "mdi:molecule",
                "multiplier": 1,
            },
            "air_quality": {
                "name": "Air Quality",
                "state_key": ATTR_AQ,
                "device_class": "aqi",
                "state_class": "measurement",
                "unit": None,
                "icon": "mdi:air-filter",
                "multiplier": 1,
            },
            "tvoc": {
                "name": "TVOC",
                "state_key": ATTR_TVOC,
                "device_class": "volatile_organic_compounds",
                "state_class": "measurement",
                "unit": "µg/m³",
                "icon": "mdi:molecule",
                "multiplier": 1,
            },
        },
        "numbers": {
            "speed": {
                "name": "Speed",
                "command_topic": "tune set speed",
                "state_key": ATTR_SPEED,
                "min": 1.0,
                "max": 4.0,
                "step": 1.0,
                "unit": None,
                "icon": "mdi:speedometer",
            }
        },
        "select": {},
        "binary_sensors": {},
    },
}

# Validate all profiles at import time
for model_key, profile in DEVICE_PROFILES.items():
    try:
        DEVICE_PROFILE_SCHEMA(profile)
    except vol.Invalid as e:
        _LOGGER.error("Invalid configuration for Duux profile '%s': %s", model_key, e)
