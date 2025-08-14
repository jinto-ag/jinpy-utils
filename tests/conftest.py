"""Common test fixtures for logger backend tests."""

# Ensure `src/` is on sys.path for local test runs (keep imports at top)
import asyncio
import json
import pathlib
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

SRC = str(pathlib.Path(__file__).resolve().parents[1] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


from jinpy_utils.logger.backends import LogEntry  # type:ignore  # noqa: E402
from jinpy_utils.logger.config import (  # type:ignore  # noqa: E402
    ConsoleBackendConfig,
    DatabaseBackendConfig,
    FileBackendConfig,
    RestApiBackendConfig,
    SecurityConfig,
    WebSocketBackendConfig,
)
from jinpy_utils.logger.enums import (  # type:ignore  # noqa: E402
    LogLevel,
    SecurityLevel,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_log_entry() -> LogEntry:
    """Create a sample log entry for testing."""
    return LogEntry(
        level=LogLevel.INFO,
        message="Test log message",
        logger_name="test.logger",
        correlation_id="test-correlation-123",
        context={"key": "value", "number": 42},
        module="test_module",
        function="test_function",
        line_number=100,
    )


@pytest.fixture
def sample_log_entries() -> list[LogEntry]:
    """Create multiple sample log entries for testing."""
    entries = []
    for i in range(5):
        entry = LogEntry(
            level=LogLevel.INFO,
            message=f"Test message {i}",
            logger_name=f"test.logger.{i}",
            correlation_id=f"correlation-{i}",
            context={"index": i, "batch": "test"},
        )
        entries.append(entry)
    return entries


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for log files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def console_config() -> ConsoleBackendConfig:
    """Create console backend configuration."""
    return ConsoleBackendConfig(
        name="test_console",
        colors=True,
        stream="stdout",
    )


@pytest.fixture
def file_config(temp_log_file: Path) -> FileBackendConfig:
    """Create file backend configuration."""
    return FileBackendConfig(
        name="test_file",
        file_path=temp_log_file,
        max_size_mb=10,
        backup_count=3,
    )


@pytest.fixture
def rest_api_config() -> RestApiBackendConfig:
    """Create REST API backend configuration."""
    return RestApiBackendConfig(
        name="test_api",
        base_url="https://api.example.com",
        endpoint="/logs",
        headers={"X-Test": "value"},
        security=SecurityConfig(
            level=SecurityLevel.API_KEY,
            api_key="test-api-key",
        ),
    )


@pytest.fixture
def websocket_config() -> WebSocketBackendConfig:
    """Create WebSocket backend configuration."""
    return WebSocketBackendConfig(
        name="test_ws",
        ws_url="wss://api.example.com/ws",
        reconnect_interval=1.0,
        ping_interval=5.0,
        security=SecurityConfig(
            level=SecurityLevel.API_KEY,
            api_key="test-ws-key",
        ),
    )


@pytest.fixture
def database_config() -> DatabaseBackendConfig:
    """Create database backend configuration."""
    return DatabaseBackendConfig(
        name="test_db",
        connection_string="sqlite:///test.db",
        table_name="test_logs",
        pool_size=2,
    )


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.ping = AsyncMock()
    mock_ws.close = AsyncMock()
    mock_ws.closed = False
    return mock_ws


@pytest.fixture
def _mock_websockets_connect():
    """Mock websockets.connect properly."""

    class MockWebSocket:
        def __init__(self):
            self.closed = False

        async def send(self, message):
            pass

        async def ping(self):
            pass

        async def close(self):
            self.closed = True

    async def mock_connect(*_args, **_kwargs):
        return MockWebSocket()

    with patch("websockets.connect", side_effect=mock_connect):
        yield


@pytest.fixture
def mock_aiohttp_session():
    """Create a mock aiohttp ClientSession with proper async context manager.

    The ``request`` attribute is an AsyncMock so tests can assert calls, while
    the returned value is an async context manager that yields a mock response.
    """
    from unittest.mock import AsyncMock

    session = AsyncMock()

    # Async context manager for responses
    class AsyncContextManager:
        def __init__(self) -> None:
            self.response = AsyncMock()
            self.response.status = 200
            self.response.text = AsyncMock(return_value="OK")

        async def __aenter__(self):
            return self.response

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None

    async def request_side_effect(*_args, **_kwargs):
        return AsyncContextManager()

    session.request = AsyncMock(side_effect=request_side_effect)
    session.closed = False
    session.close = AsyncMock()

    return session


@pytest.fixture
def current_datetime():
    """Provide a fixed datetime for testing."""
    return datetime(2023, 1, 1, 12, 0, 0)


@pytest.fixture
def mock_stats() -> dict[str, Any]:
    """Create mock backend statistics."""
    return {
        "messages_written": 100,
        "messages_failed": 2,
        "bytes_written": 5000,
        "last_write": datetime(2023, 1, 1, 12, 0, 0),
        "last_error": None,
    }


@pytest.fixture
def sample_log_dict() -> dict[str, Any]:
    """Create a sample log entry as dictionary."""
    return {
        "timestamp": "2023-01-01T12:00:00.000000",
        "level": "info",
        "message": "Test log message",
        "logger_name": "test.logger",
        "correlation_id": "test-correlation-123",
        "context": {"key": "value"},
        "module": "test_module",
        "function": "test_function",
        "line_number": 100,
    }


@pytest.fixture
def sample_log_json(sample_log_dict: dict[str, Any]) -> str:
    """Create a sample log entry as JSON string."""
    return json.dumps(sample_log_dict, separators=(",", ":"))
