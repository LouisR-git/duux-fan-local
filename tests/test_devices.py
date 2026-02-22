import voluptuous as vol
import pytest

from custom_components.duux_fan_local.devices import (
    DEVICE_PROFILE_SCHEMA,
    DEVICE_PROFILES,
)


def test_all_device_profiles_valid():
    """Test that all defined device profiles pass the Voluptuous schema validation."""
    for model_key, profile in DEVICE_PROFILES.items():
        try:
            DEVICE_PROFILE_SCHEMA(profile)
        except vol.Invalid as err:
            pytest.fail(f"Profile {model_key} failed schema validation: {err}")


def test_invalid_profile_raises_error():
    """Test that an invalid profile correctly raises a vol.Invalid error."""
    invalid_profile = {
        # Missing required 'name' key
        "fan": {"supported_features": ["turn_on"], "max_speed": 10}
    }

    with pytest.raises(vol.Invalid):
        DEVICE_PROFILE_SCHEMA(invalid_profile)

    invalid_profile_2 = {
        "name": "Bad Device",
        "fan": {"max_speed": "this should be an int"},  # Invalid type
    }

    with pytest.raises(vol.Invalid):
        DEVICE_PROFILE_SCHEMA(invalid_profile_2)
