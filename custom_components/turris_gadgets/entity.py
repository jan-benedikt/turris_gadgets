"""Shared Home Assistant entity classes for Turris Gadgets."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .hub import Peripheral, TurrisGadgetsHub


class TurrisHubEntity(Entity):
    """Base class for transmitter controls owned by the dongle."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hub: TurrisGadgetsHub) -> None:
        self.hub = hub
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, "dongle")})

    @property
    def available(self) -> bool:
        """Return whether the dongle is connected."""
        return self.hub.connected

    async def async_added_to_hass(self) -> None:
        """Subscribe to hub state updates."""
        self.async_on_remove(self.hub.add_listener(self._handle_hub_update))

    def _handle_hub_update(self, device_id: int | None) -> None:
        if device_id is None:
            self.async_write_ha_state()


class TurrisPeripheralEntity(Entity):
    """Base class for an entity belonging to a wireless peripheral."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hub: TurrisGadgetsHub, peripheral: Peripheral) -> None:
        self.hub = hub
        self.peripheral = peripheral
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{peripheral.device_id:08d}")},
            name=f"{peripheral.model} {peripheral.device_id:08d}",
            manufacturer="Jablotron",
            model=peripheral.model,
            serial_number=f"{peripheral.device_id:08d}",
            via_device=(DOMAIN, "dongle"),
        )

    @property
    def available(self) -> bool:
        """Return whether the parent dongle is connected."""
        return self.hub.connected

    async def async_added_to_hass(self) -> None:
        """Subscribe to peripheral state updates."""
        self.async_on_remove(self.hub.add_listener(self._handle_hub_update))

    def _handle_hub_update(self, device_id: int | None) -> None:
        if device_id in {None, self.peripheral.device_id}:
            self._update_from_hub()
            self.async_write_ha_state()

    def _update_from_hub(self) -> None:
        """Copy state values from the hub into entity attributes."""
