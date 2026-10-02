"""WebSocket API and sidebar panel for managing a Turris Dongle."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import probatio
from homeassistant.components import panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .connection import DongleConnectionError
from .const import (
    CONF_MODEL_OVERRIDES,
    DOMAIN,
    KNOWN_MODELS,
    PANEL_STATIC_URL,
    PANEL_URL,
    SIGNAL_PANEL_UPDATED,
    VERSION,
)
from .hub import TurrisGadgetsHub

_FRONTEND_DIR = Path(__file__).parent / "frontend"
_PANEL_MODULE = f"{PANEL_STATIC_URL}/turris-gadgets-panel.js?v={VERSION}"


def _slot(value: Any) -> int:
    """Validate a slot received from the frontend."""
    if type(value) is not int or not 0 <= value < 32:
        raise probatio.Invalid("slot must be an integer from 0 to 31")
    return value


def _device_id(value: Any) -> int:
    """Validate an eight-digit decimal peripheral identifier."""
    if type(value) is not int or not 0 <= value <= 0xFFFFFF:
        raise probatio.Invalid("device_id must be a 24-bit integer")
    return value


def _loaded_hub(hass: HomeAssistant) -> tuple[Any, TurrisGadgetsHub]:
    """Return the single loaded config entry and its runtime hub."""
    entry = next(
        (
            item
            for item in hass.config_entries.async_entries(DOMAIN)
            if item.state is ConfigEntryState.LOADED
        ),
        None,
    )
    if entry is None:
        raise HomeAssistantError("Turris Gadgets integration is not loaded")
    return entry, entry.runtime_data


def _state(hass: HomeAssistant) -> dict[str, Any]:
    """Serialize panel state without exposing implementation objects."""
    entry, hub = _loaded_hub(hass)
    by_slot = {peripheral.slot: peripheral for peripheral in hub.peripherals.values()}
    slots = []
    for number in range(32):
        peripheral = by_slot.get(number)
        slots.append(
            {
                "slot": number,
                "device_id": (
                    f"{peripheral.device_id:08d}" if peripheral is not None else None
                ),
                "model": peripheral.model if peripheral is not None else None,
                "model_overridden": (
                    peripheral is not None
                    and peripheral.device_id in hub.model_overrides
                ),
            }
        )

    observations = sorted(
        hub.scan_results.values(), key=lambda item: item.last_seen, reverse=True
    )
    return {
        "entry_id": entry.entry_id,
        "connected": hub.connected,
        "firmware": hub.firmware,
        "port": hub.port,
        "slots": slots,
        "scan_active": hub.scan_active,
        "observations": [
            {
                "device_id": f"{item.device_id:08d}",
                "model": item.model,
                "first_seen": item.first_seen.isoformat(),
                "last_seen": item.last_seen.isoformat(),
                "message_type": str(item.message_type),
                "raw": item.raw,
                "count": item.count,
            }
            for item in observations
        ],
        "rf_scan_limited": True,
    }


@websocket_api.websocket_command({probatio.Required("type"): f"{DOMAIN}/get_state"})
@websocket_api.require_admin
@callback
def websocket_get_state(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the current dongle and slot state."""
    connection.send_result(msg["id"], _state(hass))


@websocket_api.websocket_command({probatio.Required("type"): f"{DOMAIN}/subscribe"})
@websocket_api.require_admin
@callback
def websocket_subscribe(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Stream slot, connection and radio-monitor changes to the panel."""

    @callback
    def forward_update() -> None:
        try:
            connection.send_event(msg["id"], _state(hass))
        except HomeAssistantError:
            connection.send_event(msg["id"], {"loaded": False})

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, SIGNAL_PANEL_UPDATED, forward_update
    )
    connection.send_result(msg["id"])
    forward_update()


@websocket_api.websocket_command(
    {
        probatio.Required("type"): f"{DOMAIN}/set_slot",
        probatio.Required("slot"): _slot,
        probatio.Required("device_id"): _device_id,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_set_slot(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Write one peripheral to dongle flash and add its entities."""
    _, hub = _loaded_hub(hass)
    try:
        await hub.async_register_peripheral(msg["slot"], msg["device_id"])
    except (DongleConnectionError, ValueError) as err:
        raise HomeAssistantError(str(err)) from err
    connection.send_result(msg["id"], _state(hass))


@websocket_api.websocket_command(
    {
        probatio.Required("type"): f"{DOMAIN}/clear_slot",
        probatio.Required("slot"): _slot,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_clear_slot(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Clear one dongle slot and remove its entities."""
    _, hub = _loaded_hub(hass)
    try:
        await hub.async_remove_peripheral(msg["slot"])
    except (DongleConnectionError, ValueError) as err:
        raise HomeAssistantError(str(err)) from err
    connection.send_result(msg["id"], _state(hass))


@websocket_api.websocket_command(
    {
        probatio.Required("type"): f"{DOMAIN}/set_model",
        probatio.Required("device_id"): _device_id,
        probatio.Required("model"): str,
    }
)
@websocket_api.require_admin
@callback
def websocket_set_model(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Set or clear a persisted model override."""
    entry, hub = _loaded_hub(hass)
    model = msg["model"]
    if model != "auto" and model not in KNOWN_MODELS:
        raise HomeAssistantError(f"Unsupported model: {model}")
    hub.set_model_override(msg["device_id"], None if model == "auto" else model)
    overrides = {
        f"{device_id:08d}": value for device_id, value in hub.model_overrides.items()
    }
    hass.config_entries.async_update_entry(
        entry,
        options={**entry.options, CONF_MODEL_OVERRIDES: overrides},
    )
    connection.send_result(msg["id"], _state(hass))


@websocket_api.websocket_command(
    {
        probatio.Required("type"): f"{DOMAIN}/restore_slots",
        probatio.Required("slots"): list,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def websocket_restore_slots(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Replace dongle memory with the contents of a local backup."""
    entry, hub = _loaded_hub(hass)
    desired: dict[int, int] = {}
    overrides: dict[int, str] = {}
    try:
        for item in msg["slots"]:
            if not isinstance(item, dict):
                raise ValueError("Every backup slot must be an object")
            slot = _slot(item.get("slot"))
            device_id = _device_id(item.get("device_id"))
            if slot in desired:
                raise ValueError(f"Slot {slot:02d} occurs more than once")
            desired[slot] = device_id
            model = item.get("model_override")
            if model is not None:
                if model not in KNOWN_MODELS:
                    raise ValueError(f"Unsupported model: {model}")
                overrides[device_id] = model
        await hub.async_replace_slots(desired)
    except (DongleConnectionError, ValueError, probatio.Invalid) as err:
        raise HomeAssistantError(str(err)) from err

    hub.model_overrides = overrides
    for device_id in tuple(hub.peripherals):
        hub.set_model_override(device_id, overrides.get(device_id))
    hass.config_entries.async_update_entry(
        entry,
        options={
            **entry.options,
            CONF_MODEL_OVERRIDES: {
                f"{device_id:08d}": model for device_id, model in overrides.items()
            },
        },
    )
    connection.send_result(msg["id"], _state(hass))


@websocket_api.websocket_command(
    {
        probatio.Required("type"): f"{DOMAIN}/set_scan",
        probatio.Required("active"): bool,
    }
)
@websocket_api.require_admin
@callback
def websocket_set_scan(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Start or stop collecting live radio observations."""
    _, hub = _loaded_hub(hass)
    if msg["active"]:
        hub.start_scan()
    else:
        hub.stop_scan()
    connection.send_result(msg["id"], _state(hass))


async def async_setup_panel(hass: HomeAssistant) -> None:
    """Register static assets, WebSocket commands and the sidebar panel."""
    await hass.http.async_register_static_paths(
        [StaticPathConfig(PANEL_STATIC_URL, str(_FRONTEND_DIR), True)]
    )
    for command in (
        websocket_get_state,
        websocket_subscribe,
        websocket_set_slot,
        websocket_clear_slot,
        websocket_set_model,
        websocket_restore_slots,
        websocket_set_scan,
    ):
        websocket_api.async_register_command(hass, command)
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL,
        webcomponent_name="turris-gadgets-panel",
        sidebar_title="Turris Gadgets",
        sidebar_icon="mdi:radio-tower",
        module_url=_PANEL_MODULE,
        require_admin=True,
        config_panel_domain=DOMAIN,
    )
