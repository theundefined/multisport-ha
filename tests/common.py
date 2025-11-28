"""Common helpers for tests."""

from pytest_homeassistant_core.common import MockConfigEntry

from custom_components.multisport.const import DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME


def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
