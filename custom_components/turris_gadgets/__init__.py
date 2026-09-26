"""The Turris Gadgets integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .connection import DongleConnectionError
from .const import (
    CONF_DEBUG_LOGGING,
    CONF_SERIAL_PORT,
    DEFAULT_DEBUG_LOGGING,
    DOMAIN,
    NAME,
)
from .hub import TurrisGadgetsHub

type TurrisGadgetsConfigEntry = ConfigEntry[TurrisGadgetsHub]

PLATFORMS = (
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.EVENT,
    Platform.SENSOR,
    Platform.SIREN,
    Platform.SWITCH,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: TurrisGadgetsConfigEntry
) -> bool:
    """Set up Turris Gadgets from a config entry."""
    debug_logging = entry.options.get(
        CONF_DEBUG_LOGGING,
        entry.data.get(CONF_DEBUG_LOGGING, DEFAULT_DEBUG_LOGGING),
    )
    hub = TurrisGadgetsHub(entry.data[CONF_SERIAL_PORT], debug_logging=debug_logging)
    try:
        await hub.async_initialize()
    except DongleConnectionError as err:
        await hub.async_stop()
        raise ConfigEntryNotReady(str(err)) from err

    entry.runtime_data = hub
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
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
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: TurrisGadgetsConfigEntry
) -> bool:
    """Unload a Turris Gadgets config entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.async_stop()
    return True


async def _async_options_updated(
    hass: HomeAssistant, entry: TurrisGadgetsConfigEntry
) -> None:
    """Reload the integration after its runtime options change."""
    await hass.config_entries.async_reload(entry.entry_id)
