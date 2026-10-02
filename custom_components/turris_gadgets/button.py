"""Maintenance buttons for Turris Gadgets."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TurrisGadgetsConfigEntry
from .entity import TurrisHubEntity

PARALLEL_UPDATES = 0

ENROLL = ButtonEntityDescription(
    key="enroll",
    translation_key="enroll",
    entity_category=EntityCategory.CONFIG,
    entity_registry_enabled_default=False,
)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: TurrisGadgetsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up maintenance buttons."""
    async_add_entities((TurrisEnrollButton(entry.runtime_data),))


class TurrisEnrollButton(TurrisHubEntity, ButtonEntity):
    """Send a finite receiver enrollment pulse."""

    entity_description = ENROLL
    _attr_unique_id = "dongle_enroll"

    async def async_press(self) -> None:
        """Send the enrollment signal."""
        await self.hub.async_pulse_enroll()
