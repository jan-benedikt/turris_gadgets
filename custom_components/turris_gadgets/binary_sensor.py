"""Binary sensors provided by Turris Gadgets peripherals."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TurrisGadgetsConfigEntry
from .entity import TurrisPeripheralEntity
from .hub import Peripheral, TurrisGadgetsHub


@dataclass(frozen=True, kw_only=True)
class TurrisBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a peripheral binary value."""

    state_attribute: str


PRIMARY_DESCRIPTIONS = {
    "JA-81M": TurrisBinarySensorDescription(
        key="contact",
        translation_key="contact",
        state_attribute="sensor",
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    "JA-83M": TurrisBinarySensorDescription(
        key="contact",
        translation_key="contact",
        state_attribute="sensor",
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    "JA-83P": TurrisBinarySensorDescription(
        key="motion",
        translation_key="motion",
        state_attribute="sensor",
        device_class=BinarySensorDeviceClass.MOTION,
    ),
    "JA-82SH": TurrisBinarySensorDescription(
        key="vibration",
        translation_key="vibration",
        state_attribute="sensor",
        device_class=BinarySensorDeviceClass.VIBRATION,
    ),
    "JA-85ST": TurrisBinarySensorDescription(
        key="smoke",
        translation_key="smoke",
        state_attribute="sensor",
        device_class=BinarySensorDeviceClass.SMOKE,
    ),
}

TAMPER = TurrisBinarySensorDescription(
    key="tamper",
    translation_key="tamper",
    state_attribute="tamper",
    device_class=BinarySensorDeviceClass.TAMPER,
    entity_category=EntityCategory.DIAGNOSTIC,
)
LOW_BATTERY = TurrisBinarySensorDescription(
    key="low_battery",
    translation_key="low_battery",
    state_attribute="low_battery",
    device_class=BinarySensorDeviceClass.BATTERY,
    entity_category=EntityCategory.DIAGNOSTIC,
)
BLACKOUT = TurrisBinarySensorDescription(
    key="blackout",
    translation_key="blackout",
    state_attribute="blackout",
    device_class=BinarySensorDeviceClass.PROBLEM,
)
RELAY = TurrisBinarySensorDescription(
    key="relay", translation_key="relay", state_attribute="relay"
)

TAMPER_MODELS = {"JA-81M", "JA-83M", "JA-83P", "JA-82SH", "JA-85ST", "JA-80L"}
BATTERY_MODELS = {
    "JA-81M",
    "JA-83M",
    "JA-83P",
    "JA-82SH",
    "JA-85ST",
    "RC-86K",
    "TP-82N",
}


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: TurrisGadgetsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors for registered peripherals."""
    hub = entry.runtime_data
    entities: list[TurrisBinarySensor] = []
    for peripheral in hub.peripherals.values():
        descriptions: list[TurrisBinarySensorDescription] = []
        if primary := PRIMARY_DESCRIPTIONS.get(peripheral.model):
            descriptions.append(primary)
        if peripheral.model in TAMPER_MODELS:
            descriptions.append(TAMPER)
        if peripheral.model in BATTERY_MODELS:
            descriptions.append(LOW_BATTERY)
        if peripheral.model == "JA-80L":
            descriptions.append(BLACKOUT)
        if peripheral.model == "AC-88":
            descriptions.append(RELAY)
        entities.extend(
            TurrisBinarySensor(hub, peripheral, description)
            for description in descriptions
        )
    async_add_entities(entities)


class TurrisBinarySensor(TurrisPeripheralEntity, BinarySensorEntity):
    """Represent one boolean value reported by a peripheral."""

    entity_description: TurrisBinarySensorDescription

    def __init__(
        self,
        hub: TurrisGadgetsHub,
        peripheral: Peripheral,
        description: TurrisBinarySensorDescription,
    ) -> None:
        super().__init__(hub, peripheral)
        self.entity_description = description
        self._attr_unique_id = f"{peripheral.device_id:08d}_{description.key}"
        self._update_from_hub()

    def _update_from_hub(self) -> None:
        state = self.hub.states[self.peripheral.device_id]
        self._attr_is_on = getattr(state, self.entity_description.state_attribute)
