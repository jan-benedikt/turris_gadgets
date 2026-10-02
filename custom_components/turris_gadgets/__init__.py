"""The Turris Gadgets integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.typing import ConfigType

from .connection import DongleConnectionError
from .const import (
    CONF_DEBUG_LOGGING,
    CONF_MODEL_OVERRIDES,
    CONF_SERIAL_PORT,
    DEFAULT_DEBUG_LOGGING,
    DOMAIN,
    ISSUE_SERIAL_CONNECTION,
    NAME,
    SIGNAL_PANEL_UPDATED,
)
from .hub import TurrisGadgetsHub
from .panel import async_setup_panel

type TurrisGadgetsConfigEntry = ConfigEntry[TurrisGadgetsHub]

PLATFORMS = (
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.EVENT,
    Platform.SENSOR,
    Platform.SIREN,
    Platform.SWITCH,
)
_SETUP_FAILURES = f"{DOMAIN}_setup_failures"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the shared management panel and WebSocket API."""
    await async_setup_panel(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: TurrisGadgetsConfigEntry
) -> bool:
    """Set up Turris Gadgets from a config entry."""
    debug_logging = entry.options.get(
        CONF_DEBUG_LOGGING,
        entry.data.get(CONF_DEBUG_LOGGING, DEFAULT_DEBUG_LOGGING),
    )
    stored_overrides = entry.options.get(CONF_MODEL_OVERRIDES, {})
    model_overrides = {
        int(device_id): model for device_id, model in stored_overrides.items()
    }
    hub = TurrisGadgetsHub(
        entry.data[CONF_SERIAL_PORT],
        debug_logging=debug_logging,
        model_overrides=model_overrides,
    )
    try:
        await hub.async_initialize()
    except DongleConnectionError as err:
        await hub.async_stop()
        failures = hass.data.get(_SETUP_FAILURES, 0) + 1
        hass.data[_SETUP_FAILURES] = failures
        if failures >= 3:
            _create_connection_issue(hass)
        raise ConfigEntryNotReady(str(err)) from err

    hass.data.pop(_SETUP_FAILURES, None)
    ir.async_delete_issue(hass, DOMAIN, ISSUE_SERIAL_CONNECTION)
    entry.runtime_data = hub
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    def handle_hub_update(_: int | None) -> None:
        async_dispatcher_send(hass, SIGNAL_PANEL_UPDATED)
        if hub.connected:
            ir.async_delete_issue(hass, DOMAIN, ISSUE_SERIAL_CONNECTION)
        elif hub.consecutive_reconnect_failures >= 3:
            _create_connection_issue(hass)

    entry.async_on_unload(hub.add_listener(handle_hub_update))
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "dongle")},
        name=NAME,
        manufacturer="CZ.NIC / Jablotron",
        model="Turris Dongle",
        sw_version=hub.firmware,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _remove_stale_devices(hass, entry, hub)
    async_dispatcher_send(hass, SIGNAL_PANEL_UPDATED)
    return True


def _create_connection_issue(hass: HomeAssistant) -> None:
    """Report a persistent serial failure after repeated attempts."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        ISSUE_SERIAL_CONNECTION,
        is_fixable=False,
        is_persistent=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key="serial_connection_failed",
    )


def _remove_stale_devices(
    hass: HomeAssistant,
    entry: TurrisGadgetsConfigEntry,
    hub: TurrisGadgetsHub,
) -> None:
    """Remove registry entries for peripherals no longer stored in the dongle."""
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    active_identifiers = {f"{device_id:08d}" for device_id in hub.peripherals}
    for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        identifiers = {
            identifier for domain, identifier in device.identifiers if domain == DOMAIN
        }
        if "dongle" in identifiers or identifiers & active_identifiers:
            continue
        for entity in er.async_entries_for_device(entity_registry, device.id):
            entity_registry.async_remove(entity.entity_id)
        device_registry.async_remove_device(device.id)


async def async_unload_entry(
    hass: HomeAssistant, entry: TurrisGadgetsConfigEntry
) -> bool:
    """Unload a Turris Gadgets config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.async_stop()
    async_dispatcher_send(hass, SIGNAL_PANEL_UPDATED)
    return True


async def _async_options_updated(
    hass: HomeAssistant, entry: TurrisGadgetsConfigEntry
) -> None:
    """Reload only when a connection option changed."""
    hub = entry.runtime_data
    debug_logging = entry.options.get(
        CONF_DEBUG_LOGGING,
        entry.data.get(CONF_DEBUG_LOGGING, DEFAULT_DEBUG_LOGGING),
    )
    if (
        entry.data[CONF_SERIAL_PORT] != hub.port
        or debug_logging != hub.connection.debug_logging
    ):
        await hass.config_entries.async_reload(entry.entry_id)
