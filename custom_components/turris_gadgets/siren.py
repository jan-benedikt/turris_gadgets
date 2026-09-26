"""Siren controls for Turris Gadgets."""

from __future__ import annotations

from typing import Any, ClassVar

from homeassistant.components.siren import SirenEntity, SirenEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TurrisGadgetsConfigEntry
from .entity import TurrisHubEntity


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: TurrisGadgetsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up loud alarm and chime controls."""
    async_add_entities(
        (TurrisAlarmSiren(entry.runtime_data), TurrisChimeSiren(entry.runtime_data))
    )


class TurrisAlarmSiren(TurrisHubEntity, SirenEntity):
    """Represent the loud ALARM transmitter bit."""

    _attr_translation_key = "alarm"
    _attr_unique_id = "dongle_alarm"
    _attr_assumed_state = True
    _attr_supported_features = SirenEntityFeature.TURN_ON | SirenEntityFeature.TURN_OFF

    @property
    def is_on(self) -> bool:
        """Return the last alarm state sent by Home Assistant."""
        return self.hub.tx_state.alarm

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Activate the loud alarm output."""
        await self.hub.async_set_output("alarm", True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Deactivate the loud alarm output."""
        await self.hub.async_set_output("alarm", False)


class TurrisChimeSiren(TurrisHubEntity, SirenEntity):
    """Represent the slow/fast BEEP transmitter mode."""

    _attr_translation_key = "chime"
    _attr_unique_id = "dongle_chime"
    _attr_assumed_state = True
    _attr_supported_features = (
        SirenEntityFeature.TURN_ON
        | SirenEntityFeature.TURN_OFF
        | SirenEntityFeature.TONES
    )
    _attr_available_tones: ClassVar = {"SLOW": "slow", "FAST": "fast"}

    @property
    def is_on(self) -> bool:
        """Return whether a beep mode was last transmitted."""
        return self.hub.tx_state.beep != "NONE"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Activate the selected beep mode."""
        tone = str(kwargs.get("tone", "slow")).upper()
        if tone not in {"SLOW", "FAST"}:
            tone = "SLOW"
        await self.hub.async_set_output("beep", tone)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable beeping."""
        await self.hub.async_set_output("beep", "NONE")
