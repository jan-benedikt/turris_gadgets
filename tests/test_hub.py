"""Tests for slot management and the live radio monitor."""

from __future__ import annotations

import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock

PACKAGE_PATH = Path(__file__).parents[1] / "custom_components" / "turris_gadgets"
package = types.ModuleType("turris_gadgets_test")
package.__path__ = [str(PACKAGE_PATH)]
sys.modules.setdefault("turris_gadgets_test", package)
sys.modules.setdefault("serial_asyncio_fast", types.ModuleType("serial_asyncio_fast"))

hub_module = importlib.import_module("turris_gadgets_test.hub")
protocol = importlib.import_module("turris_gadgets_test.protocol")


class FakeConnection:
    """Record slot writes without opening a serial port."""

    def __init__(self) -> None:
        self.writes: list[tuple[str, int, int | None]] = []
        self.transmissions: list[protocol.TransmitState] = []
        self.transmit_error: Exception | None = None

    async def async_set_slot(self, slot: int, device_id: int) -> None:
        self.writes.append(("set", slot, device_id))

    async def async_clear_slot(self, slot: int) -> None:
        self.writes.append(("clear", slot, None))

    async def async_transmit(self, state: protocol.TransmitState) -> None:
        if self.transmit_error is not None:
            raise self.transmit_error
        self.transmissions.append(state)


class HubSlotManagementTest(unittest.IsolatedAsyncioTestCase):
    """Exercise safe updates of the dongle registration table."""

    def setUp(self) -> None:
        self.hub = hub_module.TurrisGadgetsHub("/dev/null")
        self.connection = FakeConnection()
        self.hub.connection = self.connection
        self.hub.connected = True
        self.hub.peripherals[1_572_864] = hub_module.Peripheral(0, 1_572_864, "JA-81M")

    async def test_register_and_remove_peripheral(self) -> None:
        changes: list[tuple[set[int], set[int]]] = []
        self.hub.add_peripheral_listener(
            lambda added, removed: changes.append((added, removed))
        )
        await self.hub.async_register_peripheral(4, 6_553_600)
        self.assertEqual(self.connection.writes, [("set", 4, 6_553_600)])
        self.assertEqual(self.hub.peripherals[6_553_600].slot, 4)

        await self.hub.async_remove_peripheral(4)
        self.assertEqual(self.connection.writes[-1], ("clear", 4, None))
        self.assertNotIn(6_553_600, self.hub.peripherals)
        self.assertEqual(
            changes,
            [({6_553_600}, set()), (set(), {6_553_600})],
        )

    async def test_refuses_overwrite_and_duplicate(self) -> None:
        with self.assertRaisesRegex(ValueError, "already occupied"):
            await self.hub.async_register_peripheral(0, 6_553_600)
        with self.assertRaisesRegex(ValueError, "already stored"):
            await self.hub.async_register_peripheral(4, 1_572_864)
        self.assertEqual(self.connection.writes, [])

    async def test_transmit_state_changes_only_after_success(self) -> None:
        await self.hub.async_set_output("pgx", True)
        self.assertTrue(self.hub.tx_state.pgx)
        self.assertTrue(self.connection.transmissions[-1].pgx)

        self.connection.transmit_error = hub_module.DongleConnectionError("failed")
        with self.assertRaises(hub_module.DongleConnectionError):
            await self.hub.async_set_output("pgy", True)
        self.assertFalse(self.hub.tx_state.pgy)

    async def test_replace_slots_only_writes_changes(self) -> None:
        self.hub.states[1_572_864] = hub_module.PeripheralState()
        await self.hub.async_replace_slots({0: 1_572_864, 4: 6_553_600})
        self.assertEqual(self.connection.writes, [("set", 4, 6_553_600)])

        await self.hub.async_replace_slots({5: 6_553_600})
        self.assertEqual(
            self.connection.writes[-3:],
            [("clear", 0, None), ("clear", 4, None), ("set", 5, 6_553_600)],
        )

    async def test_replace_slots_rejects_duplicate_device(self) -> None:
        with self.assertRaisesRegex(ValueError, "only occur in one slot"):
            await self.hub.async_replace_slots({1: 6_553_600, 2: 6_553_600})
        self.assertEqual(self.connection.writes, [])

    def test_model_override_can_be_set_and_cleared(self) -> None:
        changes: list[tuple[set[int], set[int]]] = []
        self.hub.add_peripheral_listener(
            lambda added, removed: changes.append((added, removed))
        )

        self.hub.set_model_override(1_572_864, "JA-83P")
        self.assertEqual(self.hub.peripherals[1_572_864].model, "JA-83P")
        self.assertEqual(self.hub.model_overrides[1_572_864], "JA-83P")

        self.hub.set_model_override(1_572_864, None)
        self.assertEqual(self.hub.peripherals[1_572_864].model, "JA-81M")
        self.assertNotIn(1_572_864, self.hub.model_overrides)
        self.assertEqual(
            changes,
            [
                ({1_572_864}, {1_572_864}),
                ({1_572_864}, {1_572_864}),
            ],
        )

    async def test_remove_cancels_pending_momentary_reset(self) -> None:
        device_id = 1_572_864
        self.hub.states[device_id] = hub_module.PeripheralState(sensor=True)
        self.hub._schedule_momentary_off(device_id, "sensor")
        task = self.hub._momentary_tasks[(device_id, "sensor")]

        await self.hub.async_remove_peripheral(0)
        await asyncio.sleep(0)

        self.assertTrue(task.cancelled())
        self.assertNotIn(device_id, self.hub.states)

    async def test_enroll_off_is_scheduled_when_pulse_is_cancelled(self) -> None:
        self.hub.async_set_output = AsyncMock()
        task = asyncio.create_task(self.hub.async_pulse_enroll())
        await asyncio.sleep(0)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        await asyncio.sleep(0)
        self.assertEqual(
            self.hub.async_set_output.await_args_list[-1].args,
            ("enroll", False),
        )


class HubRadioMonitorTest(unittest.TestCase):
    """Ensure incoming messages are aggregated while monitoring is active."""

    def test_monitor_collects_and_counts_messages(self) -> None:
        hub = hub_module.TurrisGadgetsHub("/dev/null")
        message = protocol.parse_line("[01842835] JA-81M SENSOR LB:0 ACT:1")

        hub._handle_message(message)
        self.assertEqual(hub.scan_results, {})

        hub.start_scan()
        hub._handle_message(message)
        hub._handle_message(message)
        observation = hub.scan_results[1_842_835]
        self.assertEqual(observation.count, 2)
        self.assertEqual(observation.model, "JA-81M")

        hub.stop_scan()
        hub._handle_message(message)
        self.assertEqual(observation.count, 2)

    def test_unregistered_observation_does_not_create_peripheral(self) -> None:
        hub = hub_module.TurrisGadgetsHub("/dev/null")
        hub.start_scan()
        hub._handle_message(protocol.parse_line("[01842835] JA-81M SENSOR LB:0 ACT:1"))

        self.assertIn(1_842_835, hub.scan_results)
        self.assertNotIn(1_842_835, hub.peripherals)
        self.assertNotIn(1_842_835, hub.states)


if __name__ == "__main__":
    unittest.main()
