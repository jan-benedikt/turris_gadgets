"""Tests for the standalone Turris Dongle protocol parser."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1] / "custom_components" / "turris_gadgets" / "protocol.py"
)
SPEC = importlib.util.spec_from_file_location("turris_gadgets_protocol", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
protocol = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = protocol
SPEC.loader.exec_module(protocol)


class ParseLineTest(unittest.TestCase):
    """Exercise all message families documented by CZ.NIC."""

    def test_status_messages(self) -> None:
        cases = (
            ("[01842835] JA-81M SENSOR LB:0 ACT:1", "sensor"),
            ("[01842835] JA-81M TAMPER LB:1 ACT:0", "tamper"),
            ("[06662032] JA-83P BEACON LB:0", "beacon"),
            ("[05800001] JA-80L BUTTON BLACKOUT:1", "button"),
            ("[08300001] RC-86K ARM:1 LB:0", "arm"),
            ("[08300001] RC-86K ARM:0 LB:0", "disarm"),
            ("[08300001] RC-86K PANIC LB:1", "panic"),
            ("[01842835] JA-81M DEFECT LB:0", "defect"),
            ("[13565952] AC-88 RELAY:1", "relay"),
        )
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(protocol.parse_line(raw).type, expected)

    def test_fields_are_not_conflated(self) -> None:
        message = protocol.parse_line("[05800001] JA-80L BUTTON BLACKOUT:1 LB:0")
        self.assertTrue(message.blackout)
        self.assertIsNone(message.active)
        self.assertFalse(message.low_battery)

    def test_legacy_message_id_is_accepted(self) -> None:
        numbered = protocol.parse_line("[01842835] ID:042 JA-81M SENSOR LB:0 ACT:1")
        missing = protocol.parse_line("[02439956] ID:--- TP-82N INT:21.5 C LB:1")
        self.assertEqual(numbered.model, "JA-81M")
        self.assertEqual(numbered.type, "sensor")
        self.assertTrue(numbered.active)
        self.assertEqual(missing.model, "TP-82N")
        self.assertEqual(missing.type, "internal_temperature")
        self.assertEqual(missing.temperature, 21.5)

    def test_temperatures_with_degree_byte_and_spacing(self) -> None:
        current = protocol.parse_line(b"[02439956] TP-82N INT:21.5\xb0C LB:0")
        target = protocol.parse_line("[02439956] TP-82N SET: 19.0 C LB:1")
        self.assertEqual(current.type, "internal_temperature")
        self.assertEqual(current.temperature, 21.5)
        self.assertEqual(target.type, "set_temperature")
        self.assertEqual(target.temperature, 19.0)

    def test_protocol_responses(self) -> None:
        self.assertEqual(protocol.parse_line("OK").type, "ok")
        self.assertEqual(protocol.parse_line("ERROR").type, "error")
        version = protocol.parse_line("TURRIS DONGLE V1.7 RESET")
        self.assertEqual(version.firmware, "1.7")
        occupied = protocol.parse_line("SLOT:03 [07439975]")
        empty = protocol.parse_line("SLOT:04 [--------]")
        self.assertEqual((occupied.slot, occupied.slot_device_id), (3, 7439975))
        self.assertIsNone(empty.slot_device_id)

    def test_malformed_line_is_preserved(self) -> None:
        message = protocol.parse_line("not a packet")
        self.assertEqual(message.type, "unknown")
        self.assertEqual(message.raw, "not a packet")


class CommandTest(unittest.TestCase):
    """Validate command framing and model recognition."""

    def test_command_uses_escape_prefix(self) -> None:
        self.assertEqual(protocol.identify_command(), b"\x1bWHO AM I?\n")
        self.assertEqual(protocol.get_slot_command(7), b"\x1bGET SLOT:07\n")

    def test_slot_write_commands(self) -> None:
        self.assertEqual(
            protocol.set_slot_command(3, 7_439_975),
            b"\x1bSET SLOT:03 [07439975]\n",
        )
        self.assertEqual(
            protocol.clear_slot_command(31),
            b"\x1bSET SLOT:31 [--------]\n",
        )

    def test_slot_commands_validate_input(self) -> None:
        for slot in (-1, 32):
            with self.subTest(slot=slot), self.assertRaises(ValueError):
                protocol.get_slot_command(slot)
            with self.subTest(slot=slot), self.assertRaises(ValueError):
                protocol.clear_slot_command(slot)
        for device_id in (-1, 0x1000000):
            with self.subTest(device_id=device_id), self.assertRaises(ValueError):
                protocol.set_slot_command(0, device_id)

    def test_transmit_command(self) -> None:
        state = protocol.TransmitState(pgx=True, alarm=True, beep="FAST")
        self.assertEqual(
            protocol.transmit_command(state),
            b"\x1bTX ENROLL:0 PGX:1 PGY:0 ALARM:1 BEEP:FAST\n",
        )

    def test_model_ranges(self) -> None:
        self.assertEqual(protocol.model_from_device_id(0x180000), "JA-81M")
        self.assertEqual(protocol.model_from_device_id(0x900001), "RC-86K")
        self.assertEqual(protocol.model_from_device_id(0xCF1234), "AC-88")
        self.assertEqual(protocol.model_from_device_id(1), "Unknown")


if __name__ == "__main__":
    unittest.main()
