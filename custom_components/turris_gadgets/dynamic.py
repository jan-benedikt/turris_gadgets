"""Helpers for platforms whose peripherals can change at runtime."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TurrisGadgetsConfigEntry
from .const import DOMAIN
from .hub import Peripheral

PeripheralEntityFactory = Callable[[Peripheral], Iterable[Entity]]


def setup_dynamic_entities(
    hass: HomeAssistant,
    entry: TurrisGadgetsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
    factory: PeripheralEntityFactory,
) -> None:
    """Add entities now and reconcile them when dongle slots change."""
    hub = entry.runtime_data
    entities_by_device: dict[int, list[Entity]] = {}

    def build(device_ids: set[int]) -> list[Entity]:
        entities: list[Entity] = []
        for device_id in device_ids:
            peripheral = hub.peripherals.get(device_id)
            if peripheral is None:
                continue
            device_entities = list(factory(peripheral))
            entities_by_device[device_id] = device_entities
            entities.extend(device_entities)
        return entities

    initial = build(set(hub.peripherals))
    if initial:
        async_add_entities(initial)

    @callback
    def peripheral_changed(added: set[int], removed: set[int]) -> None:
        async def reconcile() -> None:
            stale = [
                entity
                for device_id in removed
                for entity in entities_by_device.pop(device_id, [])
            ]
            if stale:
                await asyncio.gather(
                    *(entity.async_remove(force_remove=True) for entity in stale)
                )
            device_registry = dr.async_get(hass)
            entity_registry = er.async_get(hass)
            for device_id in removed - set(hub.peripherals):
                device = device_registry.async_get_device_by_identifier(
                    (DOMAIN, f"{device_id:08d}"), entry.entry_id
                )
                if device is not None and not er.async_entries_for_device(
                    entity_registry, device.id
                ):
                    device_registry.async_remove_device(device.id)
            new_entities = build(added)
            if new_entities:
                async_add_entities(new_entities)

        entry.async_create_task(
            hass,
            reconcile(),
            "reconcile Turris Gadgets entities",
        )

    entry.async_on_unload(hub.add_peripheral_listener(peripheral_changed))
