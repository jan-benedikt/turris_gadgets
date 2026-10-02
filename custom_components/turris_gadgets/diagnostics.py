"""Diagnostics support for Turris Gadgets."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import TurrisGadgetsConfigEntry
from .const import VERSION


async def async_get_config_entry_diagnostics(
    _hass: HomeAssistant, entry: TurrisGadgetsConfigEntry
) -> dict[str, Any]:
    """Return privacy-safe diagnostics for one dongle."""
    hub = entry.runtime_data
    return {
        "integration_version": VERSION,
        "connected": hub.connected,
        "firmware": hub.firmware,
        "serial_port_configured": bool(hub.port),
        "debug_logging": hub.connection.debug_logging,
        "reconnect_attempts": hub.reconnect_attempts,
        "consecutive_reconnect_failures": hub.consecutive_reconnect_failures,
        "last_error": "connection_error" if hub.last_error else None,
        "occupied_slots": len(hub.peripherals),
        "peripherals": [
            {
                "slot": peripheral.slot,
                "device_id": "REDACTED",
                "model": peripheral.model,
                "has_model_override": peripheral.device_id in hub.model_overrides,
                "has_received_message": (
                    hub.states[peripheral.device_id].last_seen is not None
                ),
            }
            for peripheral in sorted(
                hub.peripherals.values(), key=lambda item: item.slot
            )
        ],
    }
