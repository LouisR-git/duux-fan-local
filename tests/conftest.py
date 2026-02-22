import pytest


# This fixture enables the custom integration to be loaded
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield
