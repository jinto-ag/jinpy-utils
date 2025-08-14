"""Backend implementations for the logger module.

This module contains all backend implementations following the
Open/Closed principle for easy extension.
"""

import asyncio
import inspect
import json
import ssl
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, cast
from urllib.parse import urljoin

import aiofiles
import aiohttp
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from jinpy_utils.logger.config import (
    BackendConfig,
    ConsoleBackendConfig,
    FileBackendConfig,
    RestApiBackendConfig,
    WebSocketBackendConfig,
)
from jinpy_utils.logger.enums import ConnectionState, LogFormat, LogLevel
from jinpy_utils.logger.exceptions import (
    JPYLoggerBackendError,
    JPYLoggerConfigurationError,
    JPYLoggerConnectionError,
    JPYLoggerWebSocketError,
)
from jinpy_utils.utils.timing import get_current_datetime

_BACKGROUND_TASK_SINK: list[asyncio.Task] = []


class LogEntry:
    """Structured log entry with optimized serialization."""

    __slots__ = (
        "context",
        "correlation_id",
        "function",
        "level",
        "line_number",
        "logger_name",
        "message",
        "module",
        "timestamp",
    )

    def __init__(  # noqa: PLR0913
        self,
        level: LogLevel,
        message: str,
        logger_name: str,
        timestamp: datetime | None = None,
        correlation_id: str | None = None,
        context: dict[str, Any] | None = None,
        module: str | None = None,
        function: str | None = None,
        line_number: int | None = None,
    ):
        """Initialize log entry with optimized memory usage."""
        self.timestamp = timestamp or get_current_datetime()
        self.level = level
        self.message = message
        self.logger_name = logger_name
        self.correlation_id = correlation_id
        self.context = context or {}
        self.module = module
        self.function = function
        self.line_number = line_number

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "logger_name": self.logger_name,
            "correlation_id": self.correlation_id,
            "context": self.context,
            "module": self.module,
            "function": self.function,
            "line_number": self.line_number,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str, separators=(",", ":"))


class BackendInterface(ABC):
    """
    Abstract interface for logging backends following Interface Segregation.
    """

    name: str

    @abstractmethod
    async def write_async(self, entry: LogEntry) -> None:
        """Write log entry asynchronously."""
        pass

    @abstractmethod
    def write_sync(self, entry: LogEntry) -> None:
        """Write log entry synchronously."""
        pass

    @abstractmethod
    async def flush(self) -> None:
        """Flush pending entries."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close backend and cleanup resources."""
        pass

    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if backend is healthy."""
        pass

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get backend statistics."""
        pass


class BaseBackend(BackendInterface):
    """Base backend implementation with common functionality."""

    def __init__(self, config: BackendConfig):
        """Initialize base backend."""
        self.config = config
        self.name = config.name
        self._closed = False
        self._healthy = True
        self._stats: dict[str, Any] = {
            "messages_written": 0,
            "messages_failed": 0,
            "bytes_written": 0,
            "last_write": None,
            "last_error": None,
        }

        self._buffer: list[LogEntry] = []
        self._buffer_lock = asyncio.Lock()
        self._flush_task: asyncio.Task | None = None
        # Start periodic flush
        self._start_flush_timer()

    def _start_flush_timer(self) -> None:
        """Start periodic flush timer.

        This implementation avoids calling potentially mocked async methods
        (which could create un-awaited coroutines in tests) by verifying that
        the returned loop is a real ``AbstractEventLoop`` instance, and only
        then consulting its ``is_closed()`` method.
        """
        if self.config.flush_interval > 0:
            try:
                loop = asyncio.get_running_loop()
                if isinstance(loop, asyncio.AbstractEventLoop) and not loop.is_closed():
                    self._flush_task = asyncio.create_task(self._periodic_flush())
                else:
                    self._flush_task = None
            except RuntimeError:
                # No running event loop - this is fine for sync-only usage
                self._flush_task = None

    async def _periodic_flush(self) -> None:
        """Periodic flush coroutine."""
        while not self._closed:
            try:
                await asyncio.sleep(self.config.flush_interval)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._handle_error(e)

    def _handle_error(self, error: Exception) -> None:
        """Handle backend errors."""
        self._stats["messages_failed"] = self._stats["messages_failed"] + 1
        self._stats["last_error"] = str(error)
        self._healthy = False
        # Log to stderr to avoid recursion
        print(f"Backend {self.name} error: {error}", file=sys.stderr)

    def _should_write(self, entry: LogEntry) -> bool:
        """Check if entry should be written based on level."""
        return entry.level >= self.config.level

    def _format_entry(self, entry: LogEntry) -> str:
        """Format log entry based on configuration."""
        if self.config.format == LogFormat.JSON:
            return entry.to_json()
        elif self.config.format == LogFormat.PLAIN:
            return f"{entry.timestamp.isoformat()} [{entry.level.value.upper()}] {entry.logger_name}: {entry.message}"
        elif self.config.format == LogFormat.STRUCTURED:
            context_str = (
                json.dumps(entry.context, separators=(",", ":"))
                if entry.context
                else "{}"
            )
            return f"{entry.timestamp.isoformat()} [{entry.level.value.upper()}] {entry.logger_name}: {entry.message} {context_str}"
        else:
            return entry.to_json()  # Default to JSON

    async def _add_to_buffer(self, entry: LogEntry) -> None:
        """Add entry to buffer."""
        async with self._buffer_lock:
            self._buffer.append(entry)
            if len(self._buffer) >= self.config.buffer_size:
                await self._flush_buffer()

    async def _flush_buffer(self) -> None:
        """Flush buffer contents."""
        if not self._buffer:
            return

        try:
            await self._write_batch(self._buffer.copy())
            self._buffer.clear()
            self._healthy = True
        except Exception as e:
            self._handle_error(e)

    async def flush(self) -> None:
        """Flush pending entries."""
        async with self._buffer_lock:
            await self._flush_buffer()

    def is_healthy(self) -> bool:
        """Check if backend is healthy."""
        return self._healthy and not self._closed

    def get_stats(self) -> dict[str, Any]:
        """Get backend statistics."""
        return self._stats.copy()

    async def close(self) -> None:
        """Close backend and cleanup resources."""
        self._closed = True
        if self._flush_task:
            self._flush_task.cancel()
            from contextlib import suppress as _suppress  # noqa: PLC0415

            with _suppress(asyncio.CancelledError):
                await self._flush_task

        await self.flush()

    async def write_async(self, entry: LogEntry) -> None:
        """Write log entry asynchronously."""
        if self._should_write(entry):
            await self._add_to_buffer(entry)

    # ================================================= #
    # ================ Not Implemented ================ #
    # ================================================= #

    def write_sync(self, entry: LogEntry) -> None:
        """Write log entry synchronously."""
        # Default implementation that subclasses should override
        raise NotImplementedError(
            f"write_sync not implemented for {self.__class__.__name__}. "
            "Subclasses must implement this method."
        )

    async def _write_batch(self, entries: list[LogEntry]) -> None:
        """Write batch of entries (default implementation)."""
        # Default implementation that subclasses should override
        raise NotImplementedError(
            f"_write_batch not implemented for {self.__class__.__name__}. "
            "Subclasses must implement this method."
        )


class ConsoleBackend(BaseBackend):
    """High-performance console backend with color support."""

    def __init__(self, config: ConsoleBackendConfig):
        super().__init__(config)
        self.config: ConsoleBackendConfig = config
        self.stream = sys.stdout if config.stream == "stdout" else sys.stderr

        # Color codes for different log levels
        self._colors = {
            LogLevel.TRACE: "\033[90m",  # Dark gray
            LogLevel.DEBUG: "\033[36m",  # Cyan
            LogLevel.INFO: "\033[32m",  # Green
            LogLevel.WARNING: "\033[33m",  # Yellow
            LogLevel.ERROR: "\033[31m",  # Red
            LogLevel.CRITICAL: "\033[35m",  # Magenta
        }
        self._reset = "\033[0m"

    def _format_console_entry(self, entry: LogEntry) -> str:
        """Format entry for console with colors."""
        if self.config.format == LogFormat.CONSOLE:
            color = self._colors.get(entry.level, "") if self.config.colors else ""
            level_str = (
                f"{color}[{entry.level.value.upper()}]{self._reset}"
                if self.config.colors
                else f"[{entry.level.value.upper()}]"
            )

            formatted = f"{entry.timestamp.strftime('%H:%M:%S.%f')[:-3]} {level_str} {entry.logger_name}: {entry.message}"

            if entry.context:
                context_str = json.dumps(
                    entry.context, default=str, separators=(",", ":")
                )
                formatted += f" {context_str}"

            return formatted
        else:
            return self._format_entry(entry)

    async def write_async(self, entry: LogEntry) -> None:
        """Write entry asynchronously."""
        if self._should_write(entry):
            await self._add_to_buffer(entry)

    def write_sync(self, entry: LogEntry) -> None:
        """Write entry synchronously."""
        if self._should_write(entry):
            try:
                formatted = self._format_console_entry(entry)
                self.stream.write(formatted + "\n")
                self.stream.flush()
                self._stats["messages_written"] = self._stats["messages_written"] + 1
                self._stats["bytes_written"] = self._stats["bytes_written"] + len(
                    formatted.encode()
                )
                self._stats["last_write"] = get_current_datetime()
            except Exception as e:
                self._handle_error(e)

    async def _write_batch(self, entries: list[LogEntry]) -> None:
        """Write batch of entries to console."""
        try:
            output_lines = []
            total_bytes = 0

            for entry in entries:
                formatted = self._format_console_entry(entry)
                output_lines.append(formatted)
                total_bytes += len(formatted.encode())

            output = "\n".join(output_lines) + "\n"
            self.stream.write(output)
            self.stream.flush()

            self._stats["messages_written"] = self._stats["messages_written"] + len(
                entries
            )
            self._stats["bytes_written"] = self._stats["bytes_written"] + total_bytes
            self._stats["last_write"] = get_current_datetime()

        except Exception as e:
            raise JPYLoggerBackendError(
                message=f"Console write failed: {e}",
                backend_type=self.config.backend_type.value,
                backend_config={"stream": self.config.stream},
            ) from e


class FileBackend(BaseBackend):
    """High-performance async file backend with rotation."""

    def __init__(self, config: FileBackendConfig):
        super().__init__(config)
        self.config: FileBackendConfig = config
        self._file_lock = asyncio.Lock()
        # Ensure log directory exists
        self.config.file_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_compression_value(self) -> str:
        """Get compression value handling both enum and string types."""
        if hasattr(self.config.compression, "value"):
            return self.config.compression.value
        return str(self.config.compression)

    async def _rotate_if_needed(self) -> None:
        """Rotate log file if size limit is reached."""
        if not self.config.max_size_mb:
            return

        try:
            if self.config.file_path.exists():
                size_mb = self.config.file_path.stat().st_size / (1024 * 1024)
                if size_mb >= self.config.max_size_mb:
                    await self._rotate_file()
        except Exception as e:
            self._handle_error(e)

    async def _rotate_file(self) -> None:
        """Rotate log file."""
        try:
            # Move existing backup files (use filename.ext.N scheme)
            for i in range(self.config.backup_count - 1, 0, -1):
                old_file = Path(str(self.config.file_path) + f".{i}")
                new_file = Path(str(self.config.file_path) + f".{i + 1}")
                if old_file.exists():
                    old_file.rename(new_file)

            # Move current file to .1 (filename.ext.1)
            if self.config.file_path.exists():
                backup_file = Path(str(self.config.file_path) + ".1")
                self.config.file_path.rename(backup_file)

                # Compress if configured
                compression_value = self._get_compression_value()
                if compression_value != "none":
                    await self._compress_file(backup_file)

        except Exception as e:
            raise JPYLoggerBackendError(
                message=f"File rotation failed: {e}",
                backend_type=self.config.backend_type.value,
                backend_config={"file_path": str(self.config.file_path)},
            ) from e

    async def _compress_file(self, file_path: Path) -> None:
        """Compress log file based on configuration."""
        # Implementation would depend on compression type
        # For now, just a placeholder
        pass

    async def write_async(self, entry: LogEntry) -> None:
        """Write entry asynchronously."""
        if self._should_write(entry):
            await self._add_to_buffer(entry)

    def write_sync(self, entry: LogEntry) -> None:
        """Write entry synchronously."""
        if self._should_write(entry):
            try:
                formatted = self._format_entry(entry)
                with open(
                    self.config.file_path, "a", encoding=self.config.encoding
                ) as f:
                    f.write(formatted + "\n")
                    f.flush()

                self._stats["messages_written"] = self._stats["messages_written"] + 1
                self._stats["bytes_written"] = self._stats["bytes_written"] + len(
                    formatted.encode()
                )
                self._stats["last_write"] = get_current_datetime()

            except Exception as e:
                self._handle_error(e)

    async def _write_batch(self, entries: list[LogEntry]) -> None:
        """Write batch of entries to file."""
        async with self._file_lock:
            try:
                await self._rotate_if_needed()

                lines = []
                total_bytes = 0

                for entry in entries:
                    formatted = self._format_entry(entry)
                    lines.append(formatted)
                    total_bytes += len(formatted.encode())

                content = "\n".join(lines) + "\n"

                async with aiofiles.open(
                    self.config.file_path, "a", encoding=self.config.encoding
                ) as f:
                    await f.write(content)
                    await f.flush()

                self._stats["messages_written"] += len(entries)
                self._stats["bytes_written"] += total_bytes
                self._stats["last_write"] = get_current_datetime()

            except Exception as e:
                raise JPYLoggerBackendError(
                    message=f"File write failed: {e}",
                    backend_type=self.config.backend_type.value,
                    backend_config={"file_path": str(self.config.file_path)},
                ) from e


class RestApiBackend(BaseBackend):
    """REST API backend with advanced retry and security."""

    def __init__(self, config: RestApiBackendConfig):
        super().__init__(config)
        self.config: RestApiBackendConfig = config
        self._session: aiohttp.ClientSession | None = None
        self._connection_state = ConnectionState.DISCONNECTED

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with security settings."""
        if self._session is None or self._session.closed:
            headers = self.config.headers.copy()

            # Add authentication headers
            if self.config.security.api_key:
                headers["Authorization"] = f"Bearer {self.config.security.api_key}"
            elif self.config.security.oauth2_token:
                headers["Authorization"] = f"Bearer {self.config.security.oauth2_token}"

            headers["Content-Type"] = "application/json"
            headers["User-Agent"] = f"jinpy-utils-logger/{self.name}"

            # SSL configuration
            connector = None
            if not self.config.security.verify_ssl:
                connector = aiohttp.TCPConnector(ssl=False)

            timeout = aiohttp.ClientTimeout(total=self.config.timeout)

            if connector:
                self._session = aiohttp.ClientSession(
                    headers=headers,
                    timeout=timeout,
                    connector=connector,
                )
            else:
                self._session = aiohttp.ClientSession(
                    headers=headers,
                    timeout=timeout,
                )

        return self._session

    async def _send_batch(self, entries: list[LogEntry]) -> None:
        """Send batch of entries to API."""
        try:
            self._connection_state = ConnectionState.CONNECTING
            session = await self._get_session()
            url = urljoin(self.config.base_url, self.config.endpoint)

            payload = {
                "logs": [entry.to_dict() for entry in entries],
                "timestamp": get_current_datetime().isoformat(),
                "source": self.name,
                "count": len(entries),
            }

            # Make the HTTP request. ``aiohttp.ClientSession.request`` might
            # return an awaitable context manager (normal) or, when mocked,
            # could return the context manager directly. Handle both.
            request_ctx_any = session.request(self.config.method, url, json=payload)
            request_ctx_cm = (
                await request_ctx_any
                if inspect.isawaitable(request_ctx_any)
                else request_ctx_any
            )

            async with request_ctx_cm as response:
                if response.status >= 400:  # noqa: PLR2004
                    error_text = await response.text()
                    raise JPYLoggerConnectionError(
                        message=f"API request failed: {response.status}",
                        endpoint=url,
                        connection_type="http",
                        context={
                            "status": response.status,
                            "response": error_text,
                            "method": self.config.method,
                        },
                    )

            self._connection_state = ConnectionState.CONNECTED
            self._stats["messages_written"] = self._stats["messages_written"] + len(
                entries
            )
            self._stats["last_write"] = get_current_datetime()

        except JPYLoggerConnectionError:
            # Preserve connection-specific errors for tests to assert on
            self._connection_state = ConnectionState.FAILED
            raise
        except aiohttp.ClientError as e:
            self._connection_state = ConnectionState.FAILED
            raise JPYLoggerConnectionError(
                message=f"HTTP client error: {e}",
                endpoint=self.config.base_url,
                connection_type="http",
            ) from e
        except Exception as e:
            self._connection_state = ConnectionState.FAILED
            raise JPYLoggerBackendError(
                message=f"REST API backend error: {e}",
                backend_type=self.config.backend_type.value,
                backend_config={"base_url": self.config.base_url},
            ) from e

    async def write_async(self, entry: LogEntry) -> None:
        """Write entry asynchronously."""
        if self._should_write(entry):
            await self._add_to_buffer(entry)

    def write_sync(self, entry: LogEntry) -> None:
        """Write entry synchronously (queues for async processing)."""
        if self._should_write(entry):
            # Store reference for RUF006 compliance (intentionally unused)
            # Assign to a module-level sink to satisfy RUF006
            _BACKGROUND_TASK_SINK.append(asyncio.create_task(self.write_async(entry)))

    async def _write_batch(self, entries: list[LogEntry]) -> None:
        """Write batch of entries to REST API."""
        await self._send_batch(entries)

    async def close(self) -> None:
        """Close REST API backend."""
        await super().close()
        if self._session and not self._session.closed:
            await self._session.close()
        self._connection_state = ConnectionState.CLOSED


class WebSocketBackend(BaseBackend):
    """WebSocket backend for real-time log streaming."""

    def __init__(self, config: WebSocketBackendConfig):
        super().__init__(config)
        self.config: WebSocketBackendConfig = config
        self._websocket: websockets.ClientConnection | None = None
        self._connection_state = ConnectionState.DISCONNECTED
        self._reconnect_task: asyncio.Task | None = None
        self._ping_task: asyncio.Task | None = None
        # Start connection management
        self._start_connection_management()

    def _start_connection_management(self) -> None:
        """Start connection management tasks."""
        try:
            # Only start if we have an event loop
            asyncio.get_running_loop()
            self._reconnect_task = asyncio.create_task(self._connection_manager())
        except RuntimeError:
            # No event loop, will be started later
            self._reconnect_task = None

    async def _connection_manager(self) -> None:
        """Manage WebSocket connection with auto-reconnect."""
        while not self._closed:
            try:
                if self._connection_state in [
                    ConnectionState.DISCONNECTED,
                    ConnectionState.FAILED,
                ]:
                    await self._connect()

                await asyncio.sleep(self.config.reconnect_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._handle_error(e)
                await asyncio.sleep(self.config.reconnect_interval)

    async def _connect(self) -> None:
        """Connect to WebSocket server."""
        try:
            self._connection_state = ConnectionState.CONNECTING

            # Build connection kwargs
            kwargs: dict[str, Any] = {
                "max_size": self.config.max_message_size,
                "ping_interval": self.config.ping_interval,
                "ping_timeout": self.config.timeout,
            }

            # Add SSL context if needed
            if (
                self.config.ws_url.startswith("wss://")
                and not self.config.security.verify_ssl
            ):
                kwargs["ssl"] = ssl._create_unverified_context()

            # Add authentication headers
            extra_headers: dict[str, str] = {}
            if self.config.security.api_key:
                extra_headers["Authorization"] = (
                    f"Bearer {self.config.security.api_key}"
                )

            if extra_headers:
                kwargs["extra_headers"] = extra_headers

            # Connect to WebSocket. The library normally returns an awaitable,
            # but tests may stub it to return a websocket-like object directly.
            ws_connect_result = websockets.connect(
                self.config.ws_url,
                **kwargs,
            )
            if inspect.isawaitable(ws_connect_result):
                self._websocket = await ws_connect_result
            else:
                # When tests stub websockets.connect to return a connection-like object
                self._websocket = cast("Any", ws_connect_result)

            self._connection_state = ConnectionState.CONNECTED

            # Start ping task
            if self._ping_task:
                self._ping_task.cancel()
            self._ping_task = asyncio.create_task(self._ping_loop())

        except Exception as e:
            self._connection_state = ConnectionState.FAILED
            raise JPYLoggerWebSocketError(
                message=f"WebSocket connection failed: {e}",
                ws_endpoint=self.config.ws_url,
                ws_state=self._connection_state.value,
            ) from e

    async def _ping_loop(self) -> None:
        """Send periodic ping messages."""
        while not self._closed and self._websocket:
            try:
                await asyncio.sleep(self.config.ping_interval)
                if (
                    self._websocket
                    and self._connection_state == ConnectionState.CONNECTED
                    and not self._closed
                ):
                    await self._websocket.ping()

            except (ConnectionClosed, WebSocketException):
                # Update connection state when connection is closed
                self._connection_state = ConnectionState.DISCONNECTED
                self._websocket = None
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._handle_error(e)
                break

    async def _send_message(self, message: str) -> None:
        """Send message over WebSocket."""
        if not self._websocket or self._connection_state != ConnectionState.CONNECTED:
            raise JPYLoggerWebSocketError(
                message="WebSocket not connected",
                ws_endpoint=self.config.ws_url,
                ws_state=self._connection_state.value,
            )

        try:
            await self._websocket.send(message)
        except (ConnectionClosed, WebSocketException) as e:
            self._connection_state = ConnectionState.DISCONNECTED
            raise JPYLoggerWebSocketError(
                message=f"WebSocket send failed: {e}",
                ws_endpoint=self.config.ws_url,
                ws_state=self._connection_state.value,
            ) from e

    async def write_async(self, entry: LogEntry) -> None:
        """Write entry asynchronously."""
        if self._should_write(entry):
            await self._add_to_buffer(entry)

    def write_sync(self, entry: LogEntry) -> None:
        """Write entry synchronously (queues for async processing)."""
        if self._should_write(entry):
            # Store reference for RUF006 compliance (intentionally unused)
            # Assign to a module-level sink to satisfy RUF006
            _BACKGROUND_TASK_SINK.append(asyncio.create_task(self.write_async(entry)))

    async def _write_batch(self, entries: list[LogEntry]) -> None:
        """Write batch of entries over WebSocket."""
        if self._connection_state != ConnectionState.CONNECTED:
            raise JPYLoggerWebSocketError(
                message="WebSocket not connected for batch write",
                ws_endpoint=self.config.ws_url,
                ws_state=self._connection_state.value,
            )

        try:
            # Send as batch message
            batch_message = {
                "type": "log_batch",
                "timestamp": get_current_datetime().isoformat(),
                "source": self.name,
                "count": len(entries),
                "logs": [entry.to_dict() for entry in entries],
            }

            message = json.dumps(
                batch_message,
                default=str,
                separators=(",", ":"),
            )

            await self._send_message(message)

            self._stats["messages_written"] += len(entries)
            self._stats["bytes_written"] += len(message.encode())
            self._stats["last_write"] = get_current_datetime()

        except Exception as e:
            raise JPYLoggerWebSocketError(
                message=f"WebSocket batch write failed: {e}",
                ws_endpoint=self.config.ws_url,
                ws_state=self._connection_state.value,
            ) from e

    def is_healthy(self) -> bool:
        """Check if WebSocket backend is healthy."""
        return bool(
            super().is_healthy()
            and self._connection_state == ConnectionState.CONNECTED
            and self._websocket
        )

    async def close(self) -> None:
        """Close WebSocket backend."""
        await super().close()

        if self._ping_task:
            from typing import Any as _Any  # noqa: PLC0415

            cancel_result_ping: _Any = self._ping_task.cancel()
            # Await cancel() if it returned an awaitable (e.g., AsyncMock)
            import inspect as _inspect  # noqa: PLC0415  # local import to avoid top-level cost
            from contextlib import suppress as _suppress  # noqa: PLC0415

            if _inspect.isawaitable(cancel_result_ping):  # mypy: treat as runtime guard
                with _suppress(Exception):
                    await cancel_result_ping
            if isinstance(self._ping_task, asyncio.Task | asyncio.Future):
                with _suppress(asyncio.CancelledError):
                    await self._ping_task

        if self._reconnect_task:
            from typing import Any as _Any  # noqa: PLC0415

            cancel_result_reconnect: _Any = self._reconnect_task.cancel()
            import inspect as _inspect  # noqa: PLC0415  # local import to avoid top-level cost
            from contextlib import suppress as _suppress  # noqa: PLC0415

            if _inspect.isawaitable(
                cancel_result_reconnect
            ):  # mypy: treat as runtime guard
                with _suppress(Exception):
                    await cancel_result_reconnect
            if isinstance(self._reconnect_task, asyncio.Task | asyncio.Future):
                with _suppress(asyncio.CancelledError):
                    await self._reconnect_task

        if self._websocket and self._connection_state != ConnectionState.CLOSED:
            await self._websocket.close()

        self._connection_state = ConnectionState.CLOSED


# Backend factory following Factory pattern
class BackendFactory:
    """Factory for creating backend instances."""

    _backend_classes: ClassVar[dict[str, type["BackendInterface"]]] = {
        "console": ConsoleBackend,
        "file": FileBackend,
        "rest_api": RestApiBackend,
        "websocket": WebSocketBackend,
    }

    @classmethod
    def create_backend(cls, config: BackendConfig) -> BackendInterface:
        """Create backend instance from configuration."""
        # Handle both enum and string values
        backend_type = (
            config.backend_type.value
            if hasattr(config.backend_type, "value")
            else config.backend_type
        )

        backend_class = cls._backend_classes.get(backend_type)
        if not backend_class:
            raise JPYLoggerConfigurationError(
                message=f"Unsupported backend type: {backend_type}",
                config_section="backend_type",
                config_value=str(backend_type),
            )

        return backend_class(config)  # type: ignore

    @classmethod
    def register_backend(cls, backend_type: str, backend_class: Any) -> None:
        """Register new backend type."""
        cls._backend_classes[backend_type] = backend_class

    @classmethod
    def get_supported_backends(cls) -> list[str]:
        """Get list of supported backend types."""
        return list(cls._backend_classes.keys())
