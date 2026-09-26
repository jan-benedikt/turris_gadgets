"""Event entities for Turris Gadgets buttons and remote controls."""

from __future__ import annotations

from homeassistant.components.event import EventDeviceClass, EventEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TurrisGadgetsConfigEntry
from .entity import TurrisPeripheralEntity
from .hub import Peripheral, TurrisGadgetsHub

EVENT_TYPES = {
    "RC-86K": ["arm", "disarm", "panic"],
    "JA-80L": ["press"],
}


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: TurrisGadgetsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up event entities for registered peripherals."""
    hub = entry.runtime_data
    async_add_entities(
        TurrisPeripheralEvent(hub, peripheral, EVENT_TYPES[peripheral.model])
        for peripheral in hub.peripherals.values()
        if peripheral.model in EVENT_TYPES
    )


class TurrisPeripheralEvent(TurrisPeripheralEntity, EventEntity):
    """Represent stateless physical events from one peripheral."""

    _attr_device_class = EventDeviceClass.BUTTON
    _attr_translation_key = "action"

    def __init__(
        self,
        hub: TurrisGadgetsHub,
        peripheral: Peripheral,
        event_types: list[str],
    ) -> None:
        super().__init__(hub, peripheral)
        self._attr_unique_id = f"{peripheral.device_id:08d}_action"
        self._attr_event_types = event_types
        self._last_sequence = hub.states[peripheral.device_id].event_sequence

    def _update_from_hub(self) -> None:
        state = self.hub.states[self.peripheral.device_id]
        if state.event_sequence == self._last_sequence or state.last_event is None:
            return
        self._last_sequence = state.event_sequence
        if state.last_event in self._attr_event_types:
            self._trigger_event(state.last_event)
