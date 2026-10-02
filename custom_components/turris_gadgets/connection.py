"""Asynchronous serial transport for the Turris Dongle."""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Callable
from contextlib import suppress

import serial_asyncio_fast as serial_asyncio

from .const import BAUD_RATE, COMMAND_TIMEOUT
from .protocol import (
    DongleMessage,
    MessageType,
    TransmitState,
    clear_slot_command,
    get_slot_command,
    identify_command,
    parse_line,
    set_slot_command,
    transmit_command,
)

_LOGGER = logging.getLogger(__name__)


class DongleConnectionError(Exception):
    """Raised when communication with the dongle fails."""


MessageListener = Callable[[DongleMessage], None]
DisconnectListener = Callable[[], None]
MessageMatcher = Callable[[DongleMessage], bool]


class DongleConnection:
    """Own the serial stream and correlate command responses."""

    def __init__(self, port: str, *, debug_logging: bool = False) -> None:
        self.port = port
        self.debug_logging = debug_logging
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._reader_task: asyncio.Task[None] | None = None
        self._request_lock = asyncio.Lock()
        self._pending: tuple[asyncio.Future[DongleMessage], MessageMatcher] | None = (
            None
        )
        self._message_listeners: set[MessageListener] = set()
        self._disconnect_listeners: set[DisconnectListener] = set()
        self._closing = False

    @property
    def connected(self) -> bool:
        """Return whether the serial stream is open."""
        return self._writer is not None and not self._writer.is_closing()

    def add_message_listener(self, listener: MessageListener) -> Callable[[], None]:
        """Register a callback for unsolicited radio messages."""
        self._message_listeners.add(listener)
        return lambda: self._message_listeners.discard(listener)

    def add_disconnect_listener(
        self, listener: DisconnectListener
    ) -> Callable[[], None]:
        """Register a callback for an unexpected serial disconnect."""
        self._disconnect_listeners.add(listener)
        return lambda: self._disconnect_listeners.discard(listener)

    async def async_connect(self) -> None:
        """Open the serial port and start the receive loop."""
        await self.async_close()
        self._closing = False
        try:
            reader, writer = await serial_asyncio.open_serial_connection(
                url=self.port,
                baudrate=BAUD_RATE,
                bytesize=8,
                parity="N",
                stopbits=1,
            )
        except (OSError, ValueError) as err:
            raise DongleConnectionError(f"Cannot open serial port {self.port}") from err
        self._reader = reader
        self._writer = writer
        self._reader_task = asyncio.create_task(
            self._async_read_loop(), name="turris_gadgets_serial_reader"
        )

    async def async_close(self) -> None:
        """Close the serial stream and stop its receive task."""
        self._closing = True
        task = self._reader_task
        self._reader_task = None
        if task is not None and task is not asyncio.current_task():
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        if self._writer is not None:
            self._writer.close()
            with suppress(Exception):
                await self._writer.wait_closed()
        self._reader = None
        self._writer = None
        self._fail_pending(DongleConnectionError("Serial connection closed"))

    async def async_identify(self) -> str:
        """Verify the attached device and return its firmware version."""
        message = await self._async_request(
            identify_command(), lambda item: item.type is MessageType.VERSION
        )
        if message.firmware is None:
            raise DongleConnectionError("Dongle did not return a firmware version")
        return message.firmware

    async def async_read_slots(self) -> dict[int, int | None]:
        """Read all 32 registration slots."""
        slots: dict[int, int | None] = {}
        for slot in range(32):
            response = await self._async_request(
                get_slot_command(slot),
                lambda item, expected=slot: (
                    item.type is MessageType.SLOT and item.slot == expected
                ),
            )
            slots[slot] = response.slot_device_id
        return slots

    async def async_set_slot(self, slot: int, device_id: int) -> None:
        """Store one peripheral identifier in the dongle flash."""
        await self._async_write_slot(set_slot_command(slot, device_id))

    async def async_clear_slot(self, slot: int) -> None:
        """Remove one peripheral identifier from the dongle flash."""
        await self._async_write_slot(clear_slot_command(slot))

    async def _async_write_slot(self, command: bytes) -> None:
        """Write one slot and validate the dongle acknowledgement."""
        response = await self._async_request(
            command,
            lambda item: item.type in {MessageType.OK, MessageType.ERROR},
        )
        if response.type is MessageType.ERROR:
            raise DongleConnectionError("Dongle rejected slot update")

    async def async_transmit(self, state: TransmitState) -> None:
        """Transmit a receiver state three times as required by the manual."""
        command = transmit_command(state)
        for attempt in range(3):
            response = await self._async_request(
                command,
                lambda item: item.type in {MessageType.OK, MessageType.ERROR},
            )
            if response.type is MessageType.ERROR:
                raise DongleConnectionError("Dongle rejected TX command")
            if attempt < 2:
                await asyncio.sleep(random.uniform(0.2, 0.5))

    async def _async_request(
        self,
        command: bytes,
        matcher: MessageMatcher,
        timeout: float = COMMAND_TIMEOUT,
    ) -> DongleMessage:
        """Send one command and wait for its matching response."""
        async with self._request_lock:
            if not self.connected or self._writer is None:
                raise DongleConnectionError("Serial connection is not open")
            loop = asyncio.get_running_loop()
            future: asyncio.Future[DongleMessage] = loop.create_future()
            self._pending = (future, matcher)
            self._log_protocol("TX", command.rstrip(b"\r\n"))
            try:
                try:
                    self._writer.write(command)
                    await self._writer.drain()
                except (OSError, RuntimeError) as err:
                    raise DongleConnectionError("Serial write failed") from err
                async with asyncio.timeout(timeout):
                    return await future
            except TimeoutError as err:
                raise DongleConnectionError("Dongle command timed out") from err
            finally:
                if self._pending is not None and self._pending[0] is future:
                    self._pending = None

    async def _async_read_loop(self) -> None:
        """Read, parse and dispatch complete protocol lines."""
        assert self._reader is not None
        try:
            while line := await self._reader.readline():
                self._log_protocol("RX", line.rstrip(b"\r\n"))
                message = parse_line(line)
                pending = self._pending
                if pending is not None and pending[1](message):
                    if not pending[0].done():
                        pending[0].set_result(message)
                    continue
                for listener in tuple(self._message_listeners):
                    try:
                        listener(message)
                    except Exception:
                        _LOGGER.exception("Turris Gadgets message listener failed")
        except (OSError, asyncio.IncompleteReadError) as err:
            self._fail_pending(DongleConnectionError("Serial read failed", err))
        finally:
            self._reader = None
            self._writer = None
            self._fail_pending(DongleConnectionError("Serial connection lost"))
            if not self._closing:
                for listener in tuple(self._disconnect_listeners):
                    try:
                        listener()
                    except Exception:
                        _LOGGER.exception("Turris Gadgets disconnect listener failed")

    def _fail_pending(self, error: Exception) -> None:
        """Fail the current request, if there is one."""
        if self._pending is not None and not self._pending[0].done():
            self._pending[0].set_exception(error)

    def _log_protocol(self, direction: str, payload: bytes) -> None:
        """Log raw traffic when explicitly enabled by the user."""
        if self.debug_logging:
            # INFO is intentional: the UI option should work without a second
            # logger-level setting in configuration.yaml.
            _LOGGER.info("Protocol %s: %r", direction, payload)


async def async_probe(port: str, *, debug_logging: bool = False) -> str:
    """Open and identify a dongle, always releasing the port afterwards."""
    connection = DongleConnection(port, debug_logging=debug_logging)
    try:
        await connection.async_connect()
        return await connection.async_identify()
    finally:
        await connection.async_close()
