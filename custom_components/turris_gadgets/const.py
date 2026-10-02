"""Constants for the Turris Gadgets integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "turris_gadgets"
NAME: Final = "Turris Gadgets"
VERSION: Final = "0.3.0"

CONF_SERIAL_PORT: Final = "serial_port"
CONF_DEBUG_LOGGING: Final = "debug_logging"
CONF_MODEL_OVERRIDES: Final = "model_overrides"

KNOWN_MODELS: Final = (
    "AC-88",
    "JA-80L",
    "JA-81M",
    "JA-82SH",
    "JA-83M",
    "JA-83P",
    "JA-85ST",
    "RC-86K",
    "TP-82N",
)

DEFAULT_DEBUG_LOGGING: Final = False

BAUD_RATE: Final = 57_600
COMMAND_TIMEOUT: Final = 3.0
RECONNECT_MIN_DELAY: Final = 1.0
RECONNECT_MAX_DELAY: Final = 60.0
MOMENTARY_OFF_DELAY: Final = 60.0

SIGNAL_STATE_UPDATED: Final = f"{DOMAIN}_state_updated"
SIGNAL_PANEL_UPDATED: Final = f"{DOMAIN}_panel_updated"
ISSUE_SERIAL_CONNECTION: Final = "serial_connection_failed"

PANEL_URL: Final = "turris-gadgets"
PANEL_STATIC_URL: Final = "/turris_gadgets_static"

DEVICE_IMAGE_VERSION: Final = VERSION
DEVICE_IMAGE_MODELS: Final = frozenset(KNOWN_MODELS)
