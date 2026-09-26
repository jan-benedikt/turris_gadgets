"""Turris Dongle wire protocol.

This module deliberately has no Home Assistant dependency. It can therefore be
tested with captured serial lines and eventually moved into a standalone
library without changing the integration-facing API.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

COMMAND_PREFIX = b"\x1b"
COMMAND_SUFFIX = b"\n"

_DEVICE_LINE = re.compile(
    r"^\[(?P<device_id>\d{8})\]\s+(?P<model>\S+)\s+(?P<payload>.+)$"
)
_SLOT_LINE = re.compile(r"^SLOT:(?P<slot>\d{2})\s+\[(?P<device_id>\d{8}|-+)\]$")
_VERSION_LINE = re.compile(r"^TURRIS DONGLE V(?P<version>\S+?)(?:\s+RESET)?$")
_TEMPERATURE = re.compile(r"\b(?P<kind>SET|INT):\s*(?P<value>-?\d+(?:\.\d+)?)")


class MessageType(StrEnum):
    """Types emitted by the Turris Dongle."""

    OK = "ok"
    ERROR = "error"
    VERSION = "version"
    SLOT = "slot"
    SENSOR = "sensor"
    TAMPER = "tamper"
    BEACON = "beacon"
    BUTTON = "button"
    ARM = "arm"
    DISARM = "disarm"
    PANIC = "panic"
    DEFECT = "defect"
    SET_TEMPERATURE = "set_temperature"
    INTERNAL_TEMPERATURE = "internal_temperature"
    RELAY = "relay"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class DongleMessage:
    """A parsed line received from the dongle."""

    type: MessageType
    raw: str
    device_id: int | None = None
    model: str | None = None
    low_battery: bool | None = None
    active: bool | None = None
    blackout: bool | None = None
    relay: bool | None = None
    temperature: float | None = None
    slot: int | None = None
    slot_device_id: int | None = None
    firmware: str | None = None


@dataclass(frozen=True, slots=True)
class TransmitState:
    """State sent by the dongle to Turris Gadgets receivers."""

    enroll: bool = False
    pgx: bool = False
    pgy: bool = False
    alarm: bool = False
    beep: str = "NONE"

    def __post_init__(self) -> None:
        if self.beep not in {"NONE", "SLOW", "FAST"}:
            msg = f"Unsupported beep mode: {self.beep}"
            raise ValueError(msg)


def _optional_bool(payload: str, key: str) -> bool | None:
    """Return a 0/1 field from a payload, if present."""
    match = re.search(rf"(?:^|\s){re.escape(key)}:([01])(?:\s|$)", payload)
    return None if match is None else match.group(1) == "1"


def parse_line(line: bytes | str) -> DongleMessage:
    """Parse one line received from a Turris Dongle.

    Firmware encountered in the wild can include a non-ASCII degree symbol.
    Latin-1 preserves every byte while all protocol keywords remain ASCII.
    """
    if isinstance(line, bytes):
        text = line.decode("latin-1")
    else:
        text = line
    text = text.replace("\x00", "").strip()

    if text == "OK":
        return DongleMessage(MessageType.OK, text)
    if text == "ERROR":
        return DongleMessage(MessageType.ERROR, text)

    if match := _VERSION_LINE.fullmatch(text):
        return DongleMessage(
            MessageType.VERSION,
            text,
            firmware=match.group("version"),
        )

    if match := _SLOT_LINE.fullmatch(text):
        device_id = match.group("device_id")
        return DongleMessage(
            MessageType.SLOT,
            text,
            slot=int(match.group("slot")),
            slot_device_id=None if device_id.startswith("-") else int(device_id),
        )

    match = _DEVICE_LINE.fullmatch(text)
    if match is None:
        return DongleMessage(MessageType.UNKNOWN, text)

    device_id = int(match.group("device_id"))
    model = match.group("model")
    payload = match.group("payload")

    # Early firmware inserted a radio message identifier between the device
    # address and its model. ID:--- means that no identifier was available.
    if model.startswith("ID:"):
        legacy_parts = payload.split(maxsplit=1)
        if len(legacy_parts) != 2:
            return DongleMessage(MessageType.UNKNOWN, text, device_id=device_id)
        model, payload = legacy_parts

    first_token = payload.split(maxsplit=1)[0]

    message_type = {
        "SENSOR": MessageType.SENSOR,
        "TAMPER": MessageType.TAMPER,
        "BEACON": MessageType.BEACON,
        "BUTTON": MessageType.BUTTON,
        "ARM:1": MessageType.ARM,
        "ARM:0": MessageType.DISARM,
        "PANIC": MessageType.PANIC,
        "DEFECT": MessageType.DEFECT,
    }.get(first_token, MessageType.UNKNOWN)

    temperature = None
    if temperature_match := _TEMPERATURE.search(payload):
        temperature = float(temperature_match.group("value"))
        message_type = (
            MessageType.SET_TEMPERATURE
            if temperature_match.group("kind") == "SET"
            else MessageType.INTERNAL_TEMPERATURE
        )
    elif first_token.startswith("RELAY:"):
        message_type = MessageType.RELAY

    return DongleMessage(
        message_type,
        text,
        device_id=device_id,
        model=model,
        low_battery=_optional_bool(payload, "LB"),
        active=_optional_bool(payload, "ACT"),
        blackout=_optional_bool(payload, "BLACKOUT"),
        relay=_optional_bool(payload, "RELAY"),
        temperature=temperature,
    )


def encode_command(command: str) -> bytes:
    """Encode a command according to the published dongle protocol."""
    if "\n" in command or "\r" in command:
        msg = "A dongle command must contain exactly one line"
        raise ValueError(msg)
    return COMMAND_PREFIX + command.encode("ascii") + COMMAND_SUFFIX


def identify_command() -> bytes:
    """Return the command used to identify a dongle."""
    return encode_command("WHO AM I?")


def get_slot_command(slot: int) -> bytes:
    """Return the command used to read one registration slot."""
    if not 0 <= slot < 32:
        msg = f"Slot must be in range 0..31, got {slot}"
        raise ValueError(msg)
    return encode_command(f"GET SLOT:{slot:02d}")


def transmit_command(state: TransmitState) -> bytes:
    """Return a command that transmits the current receiver state."""
    command = (
        f"TX ENROLL:{int(state.enroll)} PGX:{int(state.pgx)} "
        f"PGY:{int(state.pgy)} ALARM:{int(state.alarm)} BEEP:{state.beep}"
    )
    return encode_command(command)


def model_from_device_id(device_id: int) -> str:
    """Infer the product model from its 24-bit Jablotron address."""
    ranges = (
        (0x800000, 0x87FFFF, "RC-86K"),
        (0x900000, 0x97FFFF, "RC-86K"),
        (0x180000, 0x1BFFFF, "JA-81M"),
        (0x1C0000, 0x1DFFFF, "JA-83M"),
        (0x640000, 0x65FFFF, "JA-83P"),
        (0x7F0000, 0x7FFFFF, "JA-82SH"),
        (0x760000, 0x76FFFF, "JA-85ST"),
        (0x580000, 0x59FFFF, "JA-80L"),
        (0xCF0000, 0xCFFFFF, "AC-88"),
        (0x240000, 0x25FFFF, "TP-82N"),
    )
    for start, end, model in ranges:
        if start <= device_id <= end:
            return model
    return "Unknown"
