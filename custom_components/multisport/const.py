"""Constants for the MultiSport integration."""

from datetime import timedelta
from homeassistant.const import Platform

DOMAIN = "multisport"
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

# Configuration constants
CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = timedelta(hours=1)

# Services
SERVICE_FORCE_UPDATE = "force_update"
