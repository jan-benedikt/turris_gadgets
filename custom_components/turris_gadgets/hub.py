"""Runtime model for a Turris Gadgets network."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime

from .connection import DongleConnection, DongleConnectionError
from .const import MOMENTARY_OFF_DELAY, RECONNECT_MAX_DELAY, RECONNECT_MIN_DELAY
from .protocol import DongleMessage, MessageType, TransmitState, model_from_device_id

_LOGGER = logging.getLogger(__name__)

StateListener = Callable[[int | None], None]
PeripheralListener = Callable[[set[int], set[int]], None]


@dataclass(frozen=True, slots=True)
class Peripheral:
    """A peripheral registered in a dongle slot."""

    slot: int
    device_id: int
    model: str


@dataclass(slots=True)
class PeripheralState:
    """Latest known values for a peripheral."""

    sensor: bool | None = None
    tamper: bool | None = None
    low_battery: bool | None = None
    blackout: bool | None = None
    relay: bool | None = None
    current_temperature: float | None = None
    target_temperature: float | None = None
    last_seen: datetime | None = None
    last_event: str | None = None
    event_sequence: int = 0


@dataclass(slots=True)
class RadioObservation:
    """One device observed while the live radio monitor is active."""

    device_id: int
    model: str
    first_seen: datetime
    last_seen: datetime
    message_type: str
    raw: str
    count: int = 1


class TurrisGadgetsHub:
    """Coordinate the dongle, peripherals and Home Assistant entities."""

    def __init__(
        self,
        port: str,
        *,
        debug_logging: bool = False,
        model_overrides: dict[int, str] | None = None,
    ) -> None:
        self.port = port
        self.connection = DongleConnection(port, debug_logging=debug_logging)
        self.firmware: str | None = None
        self.peripherals: dict[int, Peripheral] = {}
        self.states: dict[int, PeripheralState] = {}
        self.tx_state = TransmitState()
        self.connected = False
        self.scan_active = False
        self.scan_results: dict[int, RadioObservation] = {}
        self.model_overrides = model_overrides or {}
        self.reconnect_attempts = 0
        self.consecutive_reconnect_failures = 0
        self.last_error: str | None = None
        self._running = False
        self._listeners: set[StateListener] = set()
        self._peripheral_listeners: set[PeripheralListener] = set()
        self._reconnect_task: asyncio.Task[None] | None = None
        self._momentary_tasks: dict[tuple[int, str], asyncio.Task[None]] = {}
        self._tx_lock = asyncio.Lock()
        self.connection.add_message_listener(self._handle_message)
        self.connection.add_disconnect_listener(self._handle_disconnect)

    async def async_initialize(self) -> None:
        """Connect, identify the dongle and load registered peripherals."""
        await self.connection.async_connect()
        self.firmware = await self.connection.async_identify()
        await self.async_scan_slots()
        self.connected = True
        self._running = True

    async def async_stop(self) -> None:
        """Stop reconnects, timers and serial communication."""
        self._running = False
        if self._reconnect_task is not None:
            self._reconnect_task.cancel()
            await asyncio.gather(self._reconnect_task, return_exceptions=True)
            self._reconnect_task = None
        for task in self._momentary_tasks.values():
            task.cancel()
        if self._momentary_tasks:
            await asyncio.gather(
                *self._momentary_tasks.values(), return_exceptions=True
            )
        self._momentary_tasks.clear()
        await self.connection.async_close()
        self.connected = False

    async def async_scan_slots(self) -> None:
        """Refresh the list of peripherals stored by the dongle."""
        slots = await self.connection.async_read_slots()
        previous_ids = set(self.peripherals)
        peripherals: dict[int, Peripheral] = {}
        for slot, device_id in slots.items():
            if device_id is None:
                continue
            model = self.model_overrides.get(device_id, model_from_device_id(device_id))
            peripherals[device_id] = Peripheral(slot, device_id, model)
            self.states.setdefault(device_id, PeripheralState())
        self.peripherals = peripherals
        current_ids = set(peripherals)
        removed = previous_ids - current_ids
        for device_id in removed:
            self._remove_runtime_state(device_id)
        self._notify_peripherals(current_ids - previous_ids, removed)
        self._notify(None)

    async def async_register_peripheral(self, slot: int, device_id: int) -> None:
        """Store a peripheral in one currently empty dongle slot."""
        if not self.connected:
            raise DongleConnectionError("Dongle is not connected")
        for peripheral in self.peripherals.values():
            if peripheral.slot == slot and peripheral.device_id != device_id:
                raise ValueError(f"Slot {slot:02d} is already occupied")
            if peripheral.device_id == device_id and peripheral.slot != slot:
                raise ValueError(
                    f"Device {device_id:08d} is already stored in slot "
                    f"{peripheral.slot:02d}"
                )
        await self.connection.async_set_slot(slot, device_id)
        self.peripherals[device_id] = Peripheral(
            slot,
            device_id,
            self.model_overrides.get(device_id, model_from_device_id(device_id)),
        )
        self.states.setdefault(device_id, PeripheralState())
        self._notify_peripherals({device_id}, set())
        self._notify(None)

    async def async_remove_peripheral(self, slot: int) -> None:
        """Clear one occupied dongle slot."""
        if not self.connected:
            raise DongleConnectionError("Dongle is not connected")
        peripheral = next(
            (item for item in self.peripherals.values() if item.slot == slot), None
        )
        if peripheral is None:
            raise ValueError(f"Slot {slot:02d} is already empty")
        await self.connection.async_clear_slot(slot)
        self.peripherals.pop(peripheral.device_id, None)
        self.model_overrides.pop(peripheral.device_id, None)
        self._remove_runtime_state(peripheral.device_id)
        self._notify_peripherals(set(), {peripheral.device_id})
        self._notify(None)

    async def async_replace_slots(self, desired: dict[int, int]) -> None:
        """Replace dongle slot contents from a validated backup."""
        if not self.connected:
            raise DongleConnectionError("Dongle is not connected")
        if len(set(desired.values())) != len(desired):
            raise ValueError("A peripheral ID can only occur in one slot")
        try:
            current = {item.slot: item.device_id for item in self.peripherals.values()}
            for slot, device_id in current.items():
                if desired.get(slot) != device_id:
                    await self.async_remove_peripheral(slot)
            current = {item.slot: item.device_id for item in self.peripherals.values()}
            for slot, device_id in sorted(desired.items()):
                if current.get(slot) != device_id:
                    await self.async_register_peripheral(slot, device_id)
        except DongleConnectionError, ValueError:
            try:
                await self.async_scan_slots()
            except DongleConnectionError:
                pass
            raise

    def set_model_override(self, device_id: int, model: str | None) -> None:
        """Apply or clear a model override for a registered peripheral."""
        peripheral = self.peripherals.get(device_id)
        if peripheral is None:
            raise ValueError(f"Device {device_id:08d} is not registered")
        if model is None:
            self.model_overrides.pop(device_id, None)
            resolved_model = model_from_device_id(device_id)
        else:
            self.model_overrides[device_id] = model
            resolved_model = model
        if peripheral.model == resolved_model:
            return
        self.peripherals[device_id] = Peripheral(
            peripheral.slot, device_id, resolved_model
        )
        self._notify_peripherals({device_id}, {device_id})
        self._notify(None)

    def start_scan(self) -> None:
        """Start a fresh live monitor of messages forwarded by the dongle."""
        self.scan_results.clear()
        self.scan_active = True
        self._notify(None)

    def stop_scan(self) -> None:
        """Stop the live monitor while retaining its results."""
        self.scan_active = False
        self._notify(None)

    def add_listener(self, listener: StateListener) -> Callable[[], None]:
        """Subscribe to peripheral and connection state changes."""
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    def add_peripheral_listener(
        self, listener: PeripheralListener
    ) -> Callable[[], None]:
        """Subscribe to registered peripheral additions and removals."""
        self._peripheral_listeners.add(listener)
        return lambda: self._peripheral_listeners.discard(listener)

    async def async_set_output(self, output: str, value: bool | str) -> None:
        """Change one transmitter output and send the complete state."""
        if output not in {"pgx", "pgy", "alarm", "beep", "enroll"}:
            raise ValueError(f"Unknown transmitter output: {output}")
        async with self._tx_lock:
            new_state = replace(self.tx_state, **{output: value})
            await self.connection.async_transmit(new_state)
            self.tx_state = new_state
        self._notify(None)

    async def async_pulse_enroll(self) -> None:
        """Send a finite enrollment pulse to receiver devices."""
        await self.async_set_output("enroll", True)
        try:
            await asyncio.sleep(0.5)
        finally:
            await asyncio.shield(self.async_set_output("enroll", False))

    def _handle_message(self, message: DongleMessage) -> None:
        if message.device_id is None:
            return
        device_id = message.device_id
        now = datetime.now(UTC)
        if self.scan_active:
            if observation := self.scan_results.get(device_id):
                observation.last_seen = now
                observation.message_type = message.type
                observation.raw = message.raw
                observation.count += 1
            else:
                self.scan_results[device_id] = RadioObservation(
                    device_id=device_id,
                    model=message.model or model_from_device_id(device_id),
                    first_seen=now,
                    last_seen=now,
                    message_type=message.type,
                    raw=message.raw,
                )
        if device_id not in self.peripherals:
            return
        state = self.states.setdefault(device_id, PeripheralState())
        state.last_seen = now
        if message.low_battery is not None:
            state.low_battery = message.low_battery
        if message.blackout is not None:
            state.blackout = message.blackout
        if message.relay is not None:
            state.relay = message.relay

        if message.type is MessageType.SENSOR:
            state.sensor = message.active if message.active is not None else True
            if message.active is None:
                self._schedule_momentary_off(device_id, "sensor")
        elif message.type is MessageType.TAMPER:
            state.tamper = message.active if message.active is not None else True
            if message.active is None:
                self._schedule_momentary_off(device_id, "tamper")
        elif message.type is MessageType.INTERNAL_TEMPERATURE:
            state.current_temperature = message.temperature
        elif message.type is MessageType.SET_TEMPERATURE:
            state.target_temperature = message.temperature

        event = {
            MessageType.BUTTON: "press",
            MessageType.ARM: "arm",
            MessageType.DISARM: "disarm",
            MessageType.PANIC: "panic",
            MessageType.DEFECT: "defect",
        }.get(message.type)
        if event is not None:
            state.last_event = event
            state.event_sequence += 1
        self._notify(device_id)

    def _schedule_momentary_off(self, device_id: int, attribute: str) -> None:
        key = (device_id, attribute)
        if previous := self._momentary_tasks.pop(key, None):
            previous.cancel()

        async def turn_off() -> None:
            try:
                await asyncio.sleep(MOMENTARY_OFF_DELAY)
                if state := self.states.get(device_id):
                    setattr(state, attribute, False)
                    self._notify(device_id)
            finally:
                if self._momentary_tasks.get(key) is asyncio.current_task():
                    self._momentary_tasks.pop(key, None)

        self._momentary_tasks[key] = asyncio.create_task(
            turn_off(), name=f"turris_gadgets_{device_id}_{attribute}_off"
        )

    def _handle_disconnect(self) -> None:
        self.connected = False
        self.last_error = "Serial connection lost"
        _LOGGER.warning("Connection to Turris Dongle lost; reconnecting")
        self._notify(None)
        if self._running and (
            self._reconnect_task is None or self._reconnect_task.done()
        ):
            self._reconnect_task = asyncio.create_task(
                self._async_reconnect(), name="turris_gadgets_reconnect"
            )

    async def _async_reconnect(self) -> None:
        delay = RECONNECT_MIN_DELAY
        while self._running:
            await asyncio.sleep(delay)
            try:
                self.reconnect_attempts += 1
                await self.connection.async_connect()
                self.firmware = await self.connection.async_identify()
                await self.async_scan_slots()
            except DongleConnectionError as err:
                self.last_error = str(err)
                self.consecutive_reconnect_failures += 1
                self._notify(None)
                delay = min(delay * 2, RECONNECT_MAX_DELAY)
                continue
            self.connected = True
            self.last_error = None
            self.consecutive_reconnect_failures = 0
            self._notify(None)
            _LOGGER.info("Connection to Turris Dongle restored")
            return

    def _remove_runtime_state(self, device_id: int) -> None:
        """Remove cached values and pending momentary resets for one device."""
        self.states.pop(device_id, None)
        for key, task in tuple(self._momentary_tasks.items()):
            if key[0] == device_id:
                task.cancel()
                self._momentary_tasks.pop(key, None)

    def _notify_peripherals(self, added: set[int], removed: set[int]) -> None:
        if not added and not removed:
            return
        for listener in tuple(self._peripheral_listeners):
            listener(added, removed)

    def _notify(self, device_id: int | None) -> None:
        for listener in tuple(self._listeners):
            listener(device_id)
