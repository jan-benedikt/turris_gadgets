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


class TurrisGadgetsHub:
    """Coordinate the dongle, peripherals and Home Assistant entities."""

    def __init__(self, port: str, *, debug_logging: bool = False) -> None:
        self.port = port
        self.connection = DongleConnection(port, debug_logging=debug_logging)
        self.firmware: str | None = None
        self.peripherals: dict[int, Peripheral] = {}
        self.states: dict[int, PeripheralState] = {}
        self.tx_state = TransmitState()
        self.connected = False
        self._running = False
        self._listeners: set[StateListener] = set()
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
        peripherals: dict[int, Peripheral] = {}
        for slot, device_id in slots.items():
            if device_id is None:
                continue
            previous = self.peripherals.get(device_id)
            model = previous.model if previous else model_from_device_id(device_id)
            peripherals[device_id] = Peripheral(slot, device_id, model)
            self.states.setdefault(device_id, PeripheralState())
        self.peripherals = peripherals
        self._notify(None)

    def add_listener(self, listener: StateListener) -> Callable[[], None]:
        """Subscribe to peripheral and connection state changes."""
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    async def async_set_output(self, output: str, value: bool | str) -> None:
        """Change one transmitter output and send the complete state."""
        if output not in {"pgx", "pgy", "alarm", "beep", "enroll"}:
            raise ValueError(f"Unknown transmitter output: {output}")
        async with self._tx_lock:
            self.tx_state = replace(self.tx_state, **{output: value})
            await self.connection.async_transmit(self.tx_state)
        self._notify(None)

    async def async_pulse_enroll(self) -> None:
        """Send a finite enrollment pulse to receiver devices."""
        await self.async_set_output("enroll", True)
        await asyncio.sleep(0.5)
        await self.async_set_output("enroll", False)

    def _handle_message(self, message: DongleMessage) -> None:
        if message.device_id is None:
            return
        device_id = message.device_id
        if device_id not in self.peripherals:
            self.peripherals[device_id] = Peripheral(
                -1, device_id, message.model or model_from_device_id(device_id)
            )
        state = self.states.setdefault(device_id, PeripheralState())
        state.last_seen = datetime.now(UTC)
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
                setattr(self.states[device_id], attribute, False)
                self._notify(device_id)
            finally:
                self._momentary_tasks.pop(key, None)

        self._momentary_tasks[key] = asyncio.create_task(
            turn_off(), name=f"turris_gadgets_{device_id}_{attribute}_off"
        )

    def _handle_disconnect(self) -> None:
        self.connected = False
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
                await self.connection.async_connect()
                self.firmware = await self.connection.async_identify()
                await self.async_scan_slots()
            except DongleConnectionError:
                delay = min(delay * 2, RECONNECT_MAX_DELAY)
                continue
            self.connected = True
            self._notify(None)
            _LOGGER.info("Connection to Turris Dongle restored")
            return

    def _notify(self, device_id: int | None) -> None:
        for listener in tuple(self._listeners):
            listener(device_id)
