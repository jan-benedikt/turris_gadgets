"""Sensors provided by Turris Gadgets peripherals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TurrisGadgetsConfigEntry
from .entity import TurrisPeripheralEntity
from .hub import Peripheral, TurrisGadgetsHub


@dataclass(frozen=True, kw_only=True)
class TurrisSensorDescription(SensorEntityDescription):
    """Describe a value in PeripheralState."""

    state_attribute: str


CURRENT_TEMPERATURE = TurrisSensorDescription(
    key="current_temperature",
    translation_key="current_temperature",
    state_attribute="current_temperature",
    device_class=SensorDeviceClass.TEMPERATURE,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    state_class=SensorStateClass.MEASUREMENT,
)
TARGET_TEMPERATURE = TurrisSensorDescription(
    key="target_temperature",
    translation_key="target_temperature",
    state_attribute="target_temperature",
    device_class=SensorDeviceClass.TEMPERATURE,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    state_class=SensorStateClass.MEASUREMENT,
)
LAST_SEEN = TurrisSensorDescription(
    key="last_seen",
    translation_key="last_seen",
    state_attribute="last_seen",
    device_class=SensorDeviceClass.TIMESTAMP,
    entity_category=EntityCategory.DIAGNOSTIC,
    entity_registry_enabled_default=False,
)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: TurrisGadgetsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up read-only values for registered peripherals."""
    hub = entry.runtime_data
    entities: list[TurrisSensor] = []
    for peripheral in hub.peripherals.values():
        entities.append(TurrisSensor(hub, peripheral, LAST_SEEN))
        if peripheral.model == "TP-82N":
            entities.extend(
                (
                    TurrisSensor(hub, peripheral, CURRENT_TEMPERATURE),
                    TurrisSensor(hub, peripheral, TARGET_TEMPERATURE),
                )
            )
    async_add_entities(entities)


class TurrisSensor(TurrisPeripheralEntity, SensorEntity):
    """Represent one read-only value reported by a peripheral."""

    entity_description: TurrisSensorDescription

    def __init__(
        self,
        hub: TurrisGadgetsHub,
        peripheral: Peripheral,
        description: TurrisSensorDescription,
    ) -> None:
        super().__init__(hub, peripheral)
        self.entity_description = description
        self._attr_unique_id = f"{peripheral.device_id:08d}_{description.key}"
        self._update_from_hub()

    def _update_from_hub(self) -> None:
        state = self.hub.states[self.peripheral.device_id]
        value: float | datetime | None = getattr(
            state, self.entity_description.state_attribute
        )
        self._attr_native_value = value
