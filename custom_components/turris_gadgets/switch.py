"""PG output switches for Turris Gadgets."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TurrisGadgetsConfigEntry
from .entity import TurrisHubEntity
from .hub import TurrisGadgetsHub

OUTPUTS = (
    SwitchEntityDescription(key="pgx", translation_key="pgx"),
    SwitchEntityDescription(key="pgy", translation_key="pgy"),
)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: TurrisGadgetsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up PGX and PGY transmitter switches."""
    async_add_entities(TurrisOutputSwitch(entry.runtime_data, item) for item in OUTPUTS)


class TurrisOutputSwitch(TurrisHubEntity, SwitchEntity):
    """Represent one assumed-state transmitter output."""

    _attr_assumed_state = True

    def __init__(
        self, hub: TurrisGadgetsHub, description: SwitchEntityDescription
    ) -> None:
        super().__init__(hub)
        self.entity_description = description
        self._attr_unique_id = f"dongle_{description.key}"

    @property
    def is_on(self) -> bool:
        """Return the last state transmitted by Home Assistant."""
        return getattr(self.hub.tx_state, self.entity_description.key)

    async def async_turn_on(self, **kwargs: object) -> None:
        """Turn on the transmitter output."""
        await self.hub.async_set_output(self.entity_description.key, True)

    async def async_turn_off(self, **kwargs: object) -> None:
        """Turn off the transmitter output."""
        await self.hub.async_set_output(self.entity_description.key, False)
