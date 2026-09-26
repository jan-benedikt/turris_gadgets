"""Constants for the Turris Gadgets integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "turris_gadgets"
NAME: Final = "Turris Gadgets"

CONF_SERIAL_PORT: Final = "serial_port"
CONF_DEBUG_LOGGING: Final = "debug_logging"

DEFAULT_DEBUG_LOGGING: Final = False

BAUD_RATE: Final = 57_600
COMMAND_TIMEOUT: Final = 3.0
RECONNECT_MIN_DELAY: Final = 1.0
RECONNECT_MAX_DELAY: Final = 60.0
MOMENTARY_OFF_DELAY: Final = 60.0

SIGNAL_STATE_UPDATED: Final = f"{DOMAIN}_state_updated"
