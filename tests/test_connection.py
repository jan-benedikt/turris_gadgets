"""Tests for asynchronous serial request handling."""

from __future__ import annotations

import importlib
import sys
import types
import unittest
from pathlib import Path

PACKAGE_PATH = Path(__file__).parents[1] / "custom_components" / "turris_gadgets"
package = types.ModuleType("turris_gadgets_test")
package.__path__ = [str(PACKAGE_PATH)]
sys.modules.setdefault("turris_gadgets_test", package)
sys.modules.setdefault("serial_asyncio_fast", types.ModuleType("serial_asyncio_fast"))

connection_module = importlib.import_module("turris_gadgets_test.connection")


class FakeWriter:
    """Minimal asyncio stream writer used by request tests."""

    def __init__(self) -> None:
        self.data: list[bytes] = []
        self.drain_error: Exception | None = None

    def is_closing(self) -> bool:
        return False

    def write(self, data: bytes) -> None:
        self.data.append(data)

    async def drain(self) -> None:
        if self.drain_error is not None:
            raise self.drain_error


class FakeReader:
    """Return predefined protocol lines and then EOF."""

    def __init__(self, lines: list[bytes]) -> None:
        self.lines = iter(lines)

    async def readline(self) -> bytes:
        return next(self.lines, b"")


class ConnectionTest(unittest.IsolatedAsyncioTestCase):
    """Exercise timeouts and defensive listener dispatch."""

    async def test_request_timeout_is_normalized_and_cleared(self) -> None:
        connection = connection_module.DongleConnection("/dev/null")
        writer = FakeWriter()
        connection._writer = writer

        with self.assertRaisesRegex(
            connection_module.DongleConnectionError, "timed out"
        ):
            await connection._async_request(b"command\n", lambda _: False, 0.001)

        self.assertEqual(writer.data, [b"command\n"])
        self.assertIsNone(connection._pending)

    async def test_one_failing_listener_does_not_stop_serial_reader(self) -> None:
        connection = connection_module.DongleConnection("/dev/null")
        connection._reader = FakeReader([b"OK\n", b"ERROR\n"])
        connection._writer = FakeWriter()
        received: list[str] = []
        disconnected: list[bool] = []

        def failing_listener(_message: object) -> None:
            raise RuntimeError("listener failed")

        connection.add_message_listener(failing_listener)
        connection.add_message_listener(lambda message: received.append(message.type))
        connection.add_disconnect_listener(lambda: disconnected.append(True))

        with self.assertLogs(connection_module.__name__, level="ERROR") as logs:
            await connection._async_read_loop()

        self.assertCountEqual(received, ["ok", "error"])
        self.assertEqual(disconnected, [True])
        self.assertEqual(len(logs.output), 2)

    async def test_write_error_is_normalized(self) -> None:
        connection = connection_module.DongleConnection("/dev/null")
        writer = FakeWriter()
        writer.drain_error = OSError("disconnected")
        connection._writer = writer

        with self.assertRaisesRegex(
            connection_module.DongleConnectionError, "write failed"
        ):
            await connection._async_request(b"command\n", lambda _: False)

        self.assertIsNone(connection._pending)


if __name__ == "__main__":
    unittest.main()
