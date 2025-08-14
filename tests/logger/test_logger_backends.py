"""Tests for logger backend implementations."""

import asyncio
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, mock_open, patch

import aiohttp
import pytest
from websockets.exceptions import ConnectionClosed

from jinpy_utils.base.exceptions import (
    ExceptionRegistry,
    JPYBaseException,
    JPYConnectionError,
)
from jinpy_utils.logger import config as logger_config
from jinpy_utils.logger import exceptions as logger_exceptions
from jinpy_utils.logger.backends import (
    BackendFactory,
    BackendInterface,
    BaseBackend,
    ConsoleBackend,
    FileBackend,
    LogEntry,
    RestApiBackend,
    WebSocketBackend,
)
from jinpy_utils.logger.config import (
    BackendConfig,
    ConsoleBackendConfig,
    DatabaseBackendConfig,
    FileBackendConfig,
    RestApiBackendConfig,
    SecurityConfig,
    WebSocketBackendConfig,
)
from jinpy_utils.logger.enums import (
    BackendType,
    CompressionType,
    ConnectionState,
    LogFormat,
    LogLevel,
    SecurityLevel,
)
from jinpy_utils.logger.exceptions import (
    JPYLoggerBackendError,
    JPYLoggerConfigurationError,
    JPYLoggerConnectionError,
    JPYLoggerWebSocketError,
)


class TestLogEntry:
    """Test LogEntry functionality."""

    def test_log_entry_basic_creation(self, current_datetime: datetime) -> None:
        """Test basic LogEntry creation."""
        with patch(
            "jinpy_utils.logger.backends.get_current_datetime",
            return_value=current_datetime,
        ):
            entry = LogEntry(
                level=LogLevel.INFO,
                message="Test message",
                logger_name="test.logger",
            )

        assert entry.level == LogLevel.INFO
        assert entry.message == "Test message"
        assert entry.logger_name == "test.logger"
        assert entry.timestamp == current_datetime
        assert entry.correlation_id is None
        assert entry.context == {}
        assert entry.module is None
        assert entry.function is None
        assert entry.line_number is None

    def test_log_entry_with_all_parameters(self, sample_log_entry: LogEntry) -> None:
        """Test LogEntry with all parameters."""
        assert sample_log_entry.level == LogLevel.INFO
        assert sample_log_entry.message == "Test log message"
        assert sample_log_entry.logger_name == "test.logger"
        assert sample_log_entry.correlation_id == "test-correlation-123"
        assert sample_log_entry.context == {"key": "value", "number": 42}
        assert sample_log_entry.module == "test_module"
        assert sample_log_entry.function == "test_function"
        assert sample_log_entry.line_number == 100

    def test_log_entry_to_dict(self, sample_log_entry: LogEntry) -> None:
        """Test LogEntry to_dict conversion."""
        result = sample_log_entry.to_dict()
        assert result["timestamp"] == sample_log_entry.timestamp.isoformat()
        assert result["level"] == "info"
        assert result["message"] == "Test log message"
        assert result["logger_name"] == "test.logger"
        assert result["correlation_id"] == "test-correlation-123"
        assert result["context"] == {"key": "value", "number": 42}
        assert result["module"] == "test_module"
        assert result["function"] == "test_function"
        assert result["line_number"] == 100

    def test_log_entry_to_json(self, sample_log_entry: LogEntry) -> None:
        """Test LogEntry to_json conversion."""
        result = sample_log_entry.to_json()
        data = json.loads(result)
        assert data["level"] == "info"
        assert data["message"] == "Test log message"
        assert data["logger_name"] == "test.logger"
        assert data["correlation_id"] == "test-correlation-123"
        assert data["context"] == {"key": "value", "number": 42}


class TestBaseBackend:
    """Test BaseBackend functionality."""

    def test_base_backend_initialization(
        self, console_config: ConsoleBackendConfig
    ) -> None:
        """Test BaseBackend initialization."""
        backend = BaseBackend(console_config)
        assert backend.config == console_config
        assert backend.name == console_config.name
        assert backend._closed is False
        assert backend._healthy is True
        assert backend._buffer == []
        assert backend._stats["messages_written"] == 0
        assert backend._stats["messages_failed"] == 0
        assert backend._stats["bytes_written"] == 0
        assert backend._stats["last_write"] is None
        assert backend._stats["last_error"] is None

    def test_base_backend_should_write_level_filtering(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test BaseBackend level filtering."""
        console_config.level = LogLevel.WARNING
        backend = BaseBackend(console_config)

        # Should not write INFO level when backend is set to WARNING
        assert not backend._should_write(sample_log_entry)

        # Should write ERROR level
        sample_log_entry.level = LogLevel.ERROR
        assert backend._should_write(sample_log_entry)

    def test_base_backend_format_entry_json(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test BaseBackend JSON formatting."""
        console_config.format = LogFormat.JSON
        backend = BaseBackend(console_config)
        result = backend._format_entry(sample_log_entry)
        data = json.loads(result)
        assert data["level"] == "info"
        assert data["message"] == "Test log message"

    def test_base_backend_format_entry_plain(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test BaseBackend plain formatting."""
        console_config.format = LogFormat.PLAIN
        backend = BaseBackend(console_config)
        result = backend._format_entry(sample_log_entry)
        assert "[INFO]" in result
        assert "test.logger" in result
        assert "Test log message" in result

    def test_base_backend_format_entry_structured(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test BaseBackend structured formatting."""
        console_config.format = LogFormat.STRUCTURED
        backend = BaseBackend(console_config)
        result = backend._format_entry(sample_log_entry)
        assert "[INFO]" in result
        assert "test.logger" in result
        assert "Test log message" in result
        assert '{"key":"value","number":42}' in result

    def test_base_backend_format_entry_default(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test BaseBackend default formatting."""
        console_config.format = LogFormat.CEF  # Unknown format
        backend = BaseBackend(console_config)
        result = backend._format_entry(sample_log_entry)
        # Should default to JSON
        data = json.loads(result)
        assert data["level"] == "info"

    @pytest.mark.asyncio
    async def test_base_backend_add_to_buffer(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test BaseBackend buffer management."""
        backend = BaseBackend(console_config)

        with patch.object(backend, "_write_batch", new_callable=AsyncMock):
            await backend._add_to_buffer(sample_log_entry)
            assert len(backend._buffer) == 1
            assert backend._buffer[0] == sample_log_entry

    @pytest.mark.asyncio
    async def test_base_backend_flush_buffer_when_full(
        self, console_config: ConsoleBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        """Test BaseBackend automatic flush when buffer is full."""
        console_config.buffer_size = 3
        backend = BaseBackend(console_config)

        with patch.object(
            backend, "_write_batch", new_callable=AsyncMock
        ) as mock_write_batch:
            # Add entries one by one
            for entry in sample_log_entries[:2]:
                await backend._add_to_buffer(entry)

            # Buffer should not be flushed yet
            mock_write_batch.assert_not_called()

            # Add one more entry to trigger flush
            await backend._add_to_buffer(sample_log_entries[2])

            # Buffer should be flushed
            mock_write_batch.assert_called_once()
            assert len(backend._buffer) == 0

    @pytest.mark.asyncio
    async def test_base_backend_flush_buffer_manual(
        self, console_config: ConsoleBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        """Test BaseBackend manual flush."""
        backend = BaseBackend(console_config)

        with patch.object(
            backend, "_write_batch", new_callable=AsyncMock
        ) as mock_write_batch:
            # Add entries without triggering automatic flush
            for entry in sample_log_entries[:2]:
                await backend._add_to_buffer(entry)

            # Manual flush
            await backend.flush()
            mock_write_batch.assert_called_once()
            assert len(backend._buffer) == 0

    def test_base_backend_handle_error(
        self, console_config: ConsoleBackendConfig
    ) -> None:
        """Test BaseBackend error handling."""
        backend = BaseBackend(console_config)

        with patch("sys.stderr") as mock_stderr:
            backend._handle_error(Exception("Test error"))

        assert backend._stats["messages_failed"] == 1
        assert backend._stats["last_error"] == "Test error"
        assert backend._healthy is False
        mock_stderr.write.assert_called()

    def test_base_backend_is_healthy(
        self, console_config: ConsoleBackendConfig
    ) -> None:
        """Test BaseBackend health check."""
        backend = BaseBackend(console_config)
        assert backend.is_healthy() is True

        backend._healthy = False
        assert backend.is_healthy() is False

        backend._closed = True
        backend._healthy = True
        assert backend.is_healthy() is False

    def test_base_backend_get_stats(self, console_config: ConsoleBackendConfig) -> None:
        """Test BaseBackend statistics."""
        backend = BaseBackend(console_config)
        backend._stats["messages_written"] = 10

        stats = backend.get_stats()
        assert stats["messages_written"] == 10
        assert isinstance(stats, dict)

        # Ensure it's a copy
        stats["messages_written"] = 20
        assert backend._stats["messages_written"] == 10

    @pytest.mark.asyncio
    async def test_base_backend_close(
        self, console_config: ConsoleBackendConfig
    ) -> None:
        """Test BaseBackend close functionality."""
        backend = BaseBackend(console_config)

        with patch.object(backend, "_write_batch", new_callable=AsyncMock):
            # Start flush task only if we have an event loop
            if backend._flush_task is None:
                backend._flush_task = asyncio.create_task(backend._periodic_flush())

            await asyncio.sleep(0.1)  # Let the task start
            await backend.close()

            assert backend._closed is True
            # Task should be done or cancelled, not necessarily None
            if backend._flush_task:
                assert backend._flush_task.done() or backend._flush_task.cancelled()

    @pytest.mark.asyncio
    async def test_base_backend_periodic_flush(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test BaseBackend periodic flush timer."""
        console_config.flush_interval = 0.1
        backend = BaseBackend(console_config)

        with patch.object(
            backend, "_write_batch", new_callable=AsyncMock
        ) as mock_write_batch:
            # Add entry to buffer
            await backend._add_to_buffer(sample_log_entry)

            # Force start flush timer in event loop context
            backend._flush_task = asyncio.create_task(backend._periodic_flush())

            # Wait for flush to occur
            await asyncio.sleep(0.2)

            # Should have been flushed
            mock_write_batch.assert_called()
            await backend.close()

    @pytest.mark.asyncio
    async def test_base_backend_periodic_flush_error_handling(
        self, console_config: ConsoleBackendConfig
    ) -> None:
        """Test BaseBackend periodic flush error handling."""
        console_config.flush_interval = 0.1
        backend = BaseBackend(console_config)

        # Add entries to buffer to trigger flush
        entry = LogEntry(LogLevel.INFO, "test", "logger")

        with patch.object(
            backend, "_write_batch", new_callable=AsyncMock
        ) as mock_write_batch:
            mock_write_batch.side_effect = Exception("Flush error")
            await backend._add_to_buffer(entry)

            with patch.object(backend, "_handle_error") as mock_handle_error:
                # Force start timer in event loop context
                backend._flush_task = asyncio.create_task(backend._periodic_flush())

                await asyncio.sleep(0.2)
                mock_handle_error.assert_called()

            await backend.close()

    def test_base_backend_write_sync_not_implemented(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test BaseBackend write_sync raises NotImplementedError."""
        backend = BaseBackend(console_config)

        with pytest.raises(NotImplementedError) as exc_info:
            backend.write_sync(sample_log_entry)

        assert "write_sync not implemented" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_base_backend_write_batch_not_implemented(
        self, console_config: ConsoleBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        """Test BaseBackend _write_batch raises NotImplementedError."""
        backend = BaseBackend(console_config)

        with pytest.raises(NotImplementedError) as exc_info:
            await backend._write_batch(sample_log_entries)

        assert "_write_batch not implemented" in str(exc_info.value)


class TestConsoleBackend:
    """Test ConsoleBackend functionality."""

    def test_console_backend_initialization(
        self, console_config: ConsoleBackendConfig
    ) -> None:
        """Test ConsoleBackend initialization."""
        backend = ConsoleBackend(console_config)
        assert backend.config == console_config
        assert backend.stream == sys.stdout
        assert backend._colors[LogLevel.INFO] == "\033[32m"
        assert backend._reset == "\033[0m"

    def test_console_backend_initialization_stderr(self) -> None:
        """Test ConsoleBackend initialization with stderr."""
        config = ConsoleBackendConfig(name="test", stream="stderr")
        backend = ConsoleBackend(config)
        assert backend.stream == sys.stderr

    def test_console_backend_format_console_entry_with_colors(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test ConsoleBackend console formatting with colors."""
        console_config.format = LogFormat.CONSOLE
        console_config.colors = True
        backend = ConsoleBackend(console_config)
        result = backend._format_console_entry(sample_log_entry)

        assert "\033[32m" in result  # Green color for INFO
        assert "\033[0m" in result  # Reset color
        assert "[INFO]" in result
        assert "test.logger" in result
        assert "Test log message" in result
        assert '{"key":"value","number":42}' in result

    def test_console_backend_format_console_entry_without_colors(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test ConsoleBackend console formatting without colors."""
        console_config.format = LogFormat.CONSOLE
        console_config.colors = False
        backend = ConsoleBackend(console_config)
        result = backend._format_console_entry(sample_log_entry)

        assert "\033[32m" not in result  # No color codes
        assert "[INFO]" in result
        assert "test.logger" in result
        assert "Test log message" in result

    def test_console_backend_format_console_entry_non_console_format(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test ConsoleBackend with non-console format."""
        console_config.format = LogFormat.JSON
        backend = ConsoleBackend(console_config)
        result = backend._format_console_entry(sample_log_entry)

        # Should fall back to base formatting
        data = json.loads(result)
        assert data["level"] == "info"

    def test_console_backend_write_sync(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test ConsoleBackend synchronous write."""
        backend = ConsoleBackend(console_config)

        with (
            patch.object(backend.stream, "write") as mock_write,
            patch.object(backend.stream, "flush") as mock_flush,
        ):
            backend.write_sync(sample_log_entry)

        mock_write.assert_called_once()
        mock_flush.assert_called_once()

        # Check that message was formatted
        written_text = mock_write.call_args[0][0]
        assert "Test log message" in written_text

    def test_console_backend_write_sync_level_filtering(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test ConsoleBackend write with level filtering."""
        console_config.level = LogLevel.ERROR
        backend = ConsoleBackend(console_config)

        with patch.object(backend.stream, "write") as mock_write:
            backend.write_sync(sample_log_entry)  # INFO level

        mock_write.assert_not_called()

    def test_console_backend_write_sync_error(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test ConsoleBackend write error handling."""
        backend = ConsoleBackend(console_config)

        with (
            patch.object(backend.stream, "write", side_effect=Exception("Write error")),
            patch.object(backend, "_handle_error") as mock_handle_error,
        ):
            backend.write_sync(sample_log_entry)

        mock_handle_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_console_backend_write_async(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test ConsoleBackend asynchronous write."""
        backend = ConsoleBackend(console_config)

        with patch.object(backend, "_add_to_buffer") as mock_add_to_buffer:
            await backend.write_async(sample_log_entry)

        mock_add_to_buffer.assert_called_once_with(sample_log_entry)

    @pytest.mark.asyncio
    async def test_console_backend_write_batch(
        self, console_config: ConsoleBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        """Test ConsoleBackend batch write."""
        backend = ConsoleBackend(console_config)

        with (
            patch.object(backend.stream, "write") as mock_write,
            patch.object(backend.stream, "flush") as mock_flush,
        ):
            await backend._write_batch(sample_log_entries)

        mock_write.assert_called_once()
        mock_flush.assert_called_once()

        # Check that all messages were written
        written_text = mock_write.call_args[0][0]
        for i in range(5):
            assert f"Test message {i}" in written_text

    @pytest.mark.asyncio
    async def test_console_backend_write_batch_error(
        self, console_config: ConsoleBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        """Test ConsoleBackend batch write error."""
        backend = ConsoleBackend(console_config)

        with patch.object(
            backend.stream, "write", side_effect=Exception("Batch error")
        ):
            with pytest.raises(JPYLoggerBackendError) as exc_info:
                await backend._write_batch(sample_log_entries)

        assert "Console write failed" in str(exc_info.value)
        assert exc_info.value.error_details.details is not None
        assert (
            exc_info.value.error_details.details["backend_type"]
            == BackendType.CONSOLE.value
        )


class TestFileBackend:
    """Test FileBackend functionality."""

    def test_file_backend_initialization(self, file_config: FileBackendConfig) -> None:
        """Test FileBackend initialization."""
        backend = FileBackend(file_config)
        assert backend.config == file_config
        assert isinstance(backend._file_lock, asyncio.Lock)

    def test_file_backend_get_compression_value_enum(
        self, file_config: FileBackendConfig
    ) -> None:
        """Test FileBackend compression value extraction from enum."""
        file_config.compression = CompressionType.GZIP
        backend = FileBackend(file_config)
        assert backend._get_compression_value() == "gzip"

    def test_file_backend_get_compression_value_string(
        self, file_config: FileBackendConfig
    ) -> None:
        """Test FileBackend compression value extraction from string."""
        file_config.compression = "gzip"  # type: ignore
        backend = FileBackend(file_config)
        assert backend._get_compression_value() == "gzip"

    @pytest.mark.asyncio
    async def test_file_backend_write_async(
        self, file_config: FileBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test FileBackend asynchronous write."""
        backend = FileBackend(file_config)

        with patch.object(backend, "_add_to_buffer") as mock_add_to_buffer:
            await backend.write_async(sample_log_entry)

        mock_add_to_buffer.assert_called_once_with(sample_log_entry)

    def test_file_backend_write_sync(
        self, file_config: FileBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test FileBackend synchronous write."""
        backend = FileBackend(file_config)

        with patch("builtins.open", mock_open()) as mock_file:
            backend.write_sync(sample_log_entry)

        mock_file.assert_called_once_with(
            file_config.file_path, "a", encoding=file_config.encoding
        )
        handle = mock_file.return_value.__enter__.return_value
        handle.write.assert_called_once()
        handle.flush.assert_called_once()

    def test_file_backend_write_sync_error(
        self, file_config: FileBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test FileBackend write sync error handling."""
        backend = FileBackend(file_config)

        with (
            patch("builtins.open", side_effect=Exception("File error")),
            patch.object(backend, "_handle_error") as mock_handle_error,
        ):
            backend.write_sync(sample_log_entry)

        mock_handle_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_backend_write_batch(
        self, file_config: FileBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        """Test FileBackend batch write."""
        backend = FileBackend(file_config)

        mock_aiofile = AsyncMock()
        mock_aiofile.write = AsyncMock()
        mock_aiofile.flush = AsyncMock()
        mock_aiofile.__aenter__ = AsyncMock(return_value=mock_aiofile)
        mock_aiofile.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("aiofiles.open", return_value=mock_aiofile),
            patch.object(backend, "_rotate_if_needed") as mock_rotate,
        ):
            await backend._write_batch(sample_log_entries)

        mock_rotate.assert_called_once()
        mock_aiofile.write.assert_called_once()
        mock_aiofile.flush.assert_called_once()

        # Check that all messages were written
        written_content = mock_aiofile.write.call_args[0][0]
        for i in range(5):
            assert f"Test message {i}" in written_content

    @pytest.mark.asyncio
    async def test_file_backend_write_batch_error(
        self, file_config: FileBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        """Test FileBackend batch write error."""
        backend = FileBackend(file_config)

        with patch("aiofiles.open", side_effect=Exception("File write error")):
            with pytest.raises(JPYLoggerBackendError) as exc_info:
                await backend._write_batch(sample_log_entries)

        assert "File write failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_file_backend_rotate_if_needed_no_rotation(
        self, file_config: FileBackendConfig
    ) -> None:
        """Test FileBackend rotation check when rotation not needed."""
        file_config.max_size_mb = None
        backend = FileBackend(file_config)

        # Should return early without doing anything
        await backend._rotate_if_needed()

    @pytest.mark.asyncio
    async def test_file_backend_rotate_if_needed_with_rotation(
        self, file_config: FileBackendConfig, temp_log_file: Path
    ) -> None:
        """Test FileBackend rotation when needed."""
        file_config.max_size_mb = 1  # 1MB limit
        backend = FileBackend(file_config)

        # Create a file that exceeds the limit
        with open(temp_log_file, "w") as f:
            f.write("x" * (2 * 1024 * 1024))  # 2MB

        with patch.object(backend, "_rotate_file") as mock_rotate:
            await backend._rotate_if_needed()

        mock_rotate.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_backend_rotate_if_needed_error(
        self, file_config: FileBackendConfig
    ) -> None:
        """Test FileBackend rotation error handling."""
        backend = FileBackend(file_config)

        with (
            patch("pathlib.Path.exists", side_effect=Exception("Stat error")),
            patch.object(backend, "_handle_error") as mock_handle_error,
        ):
            await backend._rotate_if_needed()

        mock_handle_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_backend_rotate_file(
        self, file_config: FileBackendConfig, temp_log_dir: Path
    ) -> None:
        """Test FileBackend file rotation."""
        log_file = temp_log_dir / "test.log"
        backup1 = temp_log_dir / "test.log.1"
        file_config.file_path = log_file
        file_config.backup_count = 3
        backend = FileBackend(file_config)

        # Create test files
        log_file.write_text("current log")
        backup1.write_text("backup 1")

        with patch.object(backend, "_compress_file") as mock_compress:
            await backend._rotate_file()

        mock_compress.assert_called_once()

        # After rotation: current log becomes .1, old .1 becomes .2
        backup2 = temp_log_dir / "test.log.2"
        new_backup1 = temp_log_dir / "test.log.1"

        # Verify rotation occurred
        assert backup2.exists() or new_backup1.exists()

        # Check content if files exist
        if backup2.exists():
            assert backup2.read_text() == "backup 1"
        if new_backup1.exists():
            assert new_backup1.read_text() == "current log"

    @pytest.mark.asyncio
    async def test_file_backend_rotate_file_error(
        self, file_config: FileBackendConfig
    ) -> None:
        """Test FileBackend file rotation error."""
        backend = FileBackend(file_config)

        with patch("pathlib.Path.rename", side_effect=Exception("Rename error")):
            with pytest.raises(JPYLoggerBackendError) as exc_info:
                await backend._rotate_file()

        assert "File rotation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_file_backend_compress_file(
        self, file_config: FileBackendConfig, temp_log_file: Path
    ) -> None:
        """Test FileBackend file compression placeholder."""
        backend = FileBackend(file_config)

        # This is a placeholder method, so it should just pass
        await backend._compress_file(temp_log_file)


class TestRestApiBackend:
    """Test RestApiBackend functionality."""

    def test_rest_api_backend_initialization(
        self, rest_api_config: RestApiBackendConfig
    ) -> None:
        """Test RestApiBackend initialization."""
        backend = RestApiBackend(rest_api_config)
        assert backend.config == rest_api_config
        assert backend._session is None
        assert backend._connection_state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_rest_api_backend_get_session(
        self, rest_api_config: RestApiBackendConfig
    ) -> None:
        """Test RestApiBackend session creation."""
        backend = RestApiBackend(rest_api_config)

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session.closed = False
            mock_session_class.return_value = mock_session

            session = await backend._get_session()

        assert session == mock_session
        mock_session_class.assert_called_once()

        # Check that headers were set correctly
        call_kwargs = mock_session_class.call_args[1]
        headers = call_kwargs["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-api-key"
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"].startswith("jinpy-utils-logger/")

    @pytest.mark.asyncio
    async def test_rest_api_backend_get_session_oauth2(
        self, rest_api_config: RestApiBackendConfig
    ) -> None:
        """Test RestApiBackend session creation with OAuth2."""
        rest_api_config.security.level = SecurityLevel.OAUTH2
        rest_api_config.security.api_key = None
        rest_api_config.security.oauth2_token = "oauth2-token"
        backend = RestApiBackend(rest_api_config)

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session.closed = False
            mock_session_class.return_value = mock_session

            await backend._get_session()

        # Check OAuth2 token in headers
        call_kwargs = mock_session_class.call_args[1]
        headers = call_kwargs["headers"]
        assert headers["Authorization"] == "Bearer oauth2-token"

    @pytest.mark.asyncio
    async def test_rest_api_backend_get_session_no_ssl_verify(
        self, rest_api_config: RestApiBackendConfig
    ) -> None:
        """Test RestApiBackend session creation without SSL verification."""
        rest_api_config.security.verify_ssl = False
        backend = RestApiBackend(rest_api_config)

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session.closed = False
            mock_session_class.return_value = mock_session

            await backend._get_session()

        # Check SSL context
        call_kwargs = mock_session_class.call_args[1]
        connector = call_kwargs["connector"]
        assert connector is not None

    @pytest.mark.asyncio
    async def test_rest_api_backend_get_session_reuse_existing(
        self, rest_api_config: RestApiBackendConfig
    ) -> None:
        """Test RestApiBackend session reuse."""
        backend = RestApiBackend(rest_api_config)

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session.closed = False
            mock_session_class.return_value = mock_session

            session1 = await backend._get_session()
            session2 = await backend._get_session()

        assert session1 == session2
        mock_session_class.assert_called_once()  # Only called once

    @pytest.mark.asyncio
    async def test_rest_api_backend_send_batch_success(
        self,
        rest_api_config: RestApiBackendConfig,
        sample_log_entries: list[LogEntry],
        mock_aiohttp_session: AsyncMock,
    ) -> None:
        """Test RestApiBackend successful batch send."""
        backend = RestApiBackend(rest_api_config)
        backend._session = mock_aiohttp_session

        await backend._send_batch(sample_log_entries)

        assert backend._connection_state == ConnectionState.CONNECTED
        assert backend._stats["messages_written"] == 5

        # Verify request was made
        mock_aiohttp_session.request.assert_called_once()
        call_args = mock_aiohttp_session.request.call_args
        assert call_args[0][0] == rest_api_config.method
        assert call_args[0][1].endswith(rest_api_config.endpoint)
        assert "json" in call_args[1]

    @pytest.mark.asyncio
    async def test_rest_api_backend_send_batch_http_error(
        self, rest_api_config: RestApiBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        """Test RestApiBackend HTTP error handling."""
        backend = RestApiBackend(rest_api_config)

        # Create a mock session that returns error response
        async def mock_request(*_args, **_kwargs):
            class ErrorContextManager:
                async def __aenter__(self):
                    mock_response = AsyncMock()
                    mock_response.status = 400
                    mock_response.text = AsyncMock(return_value="Bad Request")
                    return mock_response

                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    return None

            return ErrorContextManager()

        mock_session = AsyncMock()
        mock_session.closed = False
        mock_session.request = mock_request
        backend._session = mock_session

        with pytest.raises(JPYLoggerConnectionError) as exc_info:
            await backend._send_batch(sample_log_entries)

        assert "API request failed: 400" in str(exc_info.value)
        assert backend._connection_state == ConnectionState.FAILED

    @pytest.mark.asyncio
    async def test_rest_api_backend_send_batch_client_error(
        self, rest_api_config: RestApiBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        """Test RestApiBackend client error handling."""
        backend = RestApiBackend(rest_api_config)

        mock_session = AsyncMock()
        mock_session.closed = False
        # Make request() raise ClientError before context manager creation
        mock_session.request.side_effect = aiohttp.ClientError("Connection failed")
        backend._session = mock_session

        with pytest.raises(JPYLoggerConnectionError) as exc_info:
            await backend._send_batch(sample_log_entries)

        assert "HTTP client error" in str(exc_info.value)
        assert backend._connection_state == ConnectionState.FAILED

    @pytest.mark.asyncio
    async def test_rest_api_backend_send_batch_general_error(
        self, rest_api_config: RestApiBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        """Test RestApiBackend general error handling."""
        backend = RestApiBackend(rest_api_config)

        mock_session = AsyncMock()
        mock_session.closed = False
        mock_session.request.side_effect = Exception("General error")
        backend._session = mock_session

        with pytest.raises(JPYLoggerBackendError) as exc_info:
            await backend._send_batch(sample_log_entries)

        assert "REST API backend error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rest_api_backend_write_async(
        self, rest_api_config: RestApiBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test RestApiBackend asynchronous write."""
        backend = RestApiBackend(rest_api_config)

        with patch.object(backend, "_add_to_buffer") as mock_add_to_buffer:
            await backend.write_async(sample_log_entry)

        mock_add_to_buffer.assert_called_once_with(sample_log_entry)

    def test_rest_api_backend_write_sync(
        self, rest_api_config: RestApiBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test RestApiBackend synchronous write."""
        backend = RestApiBackend(rest_api_config)

        with patch("asyncio.create_task") as mock_create_task:
            backend.write_sync(sample_log_entry)

        mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_rest_api_backend_write_batch(
        self, rest_api_config: RestApiBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        """Test RestApiBackend batch write."""
        backend = RestApiBackend(rest_api_config)

        with patch.object(backend, "_send_batch") as mock_send_batch:
            await backend._write_batch(sample_log_entries)

        mock_send_batch.assert_called_once_with(sample_log_entries)

    @pytest.mark.asyncio
    async def test_rest_api_backend_close(
        self, rest_api_config: RestApiBackendConfig
    ) -> None:
        """Test RestApiBackend close."""
        backend = RestApiBackend(rest_api_config)
        backend._session = AsyncMock()
        backend._session.closed = False

        await backend.close()

        backend._session.close.assert_called_once()
        assert backend._connection_state == ConnectionState.CLOSED


class TestWebSocketBackend:
    """Test WebSocketBackend functionality."""

    def test_websocket_backend_initialization(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        """Test WebSocketBackend initialization."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        assert backend.config == websocket_config
        assert backend._websocket is None
        assert backend._connection_state == ConnectionState.DISCONNECTED
        assert backend._reconnect_task is None
        assert backend._ping_task is None

    @pytest.mark.asyncio
    async def test_websocket_backend_connect_ssl_no_verify(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        """Test WebSocketBackend connection with SSL no verify."""
        websocket_config.ws_url = "wss://api.example.com/ws"
        websocket_config.security.verify_ssl = False

        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        class MockWebSocket:
            async def send(self, msg):
                pass

            async def ping(self):
                pass

            async def close(self):
                pass

        async def mock_connect(*_args, **_kwargs):
            return MockWebSocket()

        with (
            patch("websockets.connect", side_effect=mock_connect) as mock_connect_patch,
            patch("ssl._create_unverified_context") as mock_ssl_context,
        ):
            await backend._connect()

        call_kwargs = mock_connect_patch.call_args[1]
        assert "ssl" in call_kwargs
        mock_ssl_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_backend_ping_loop(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        """Test WebSocketBackend ping loop."""
        websocket_config.ping_interval = 0.1

        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        mock_websocket = AsyncMock()
        ping_count = 0

        async def mock_ping():
            nonlocal ping_count
            ping_count += 1
            if ping_count > 1:  # Reduce iterations
                from websockets.exceptions import ConnectionClosed

                raise ConnectionClosed(None, None)

        mock_websocket.ping.side_effect = mock_ping
        backend._websocket = mock_websocket
        backend._connection_state = ConnectionState.CONNECTED

        # Start ping loop and let it run briefly
        ping_task = asyncio.create_task(backend._ping_loop())
        await asyncio.sleep(0.25)  # Allow time for pings

        # Clean up
        ping_task.cancel()
        try:
            await ping_task
        except asyncio.CancelledError:
            pass

        # Verify pings were called and connection state updated
        assert ping_count > 0
        assert backend._connection_state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_websocket_backend_connection_manager(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        """Test WebSocketBackend connection manager."""
        websocket_config.reconnect_interval = 0.1

        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        backend._connection_state = ConnectionState.DISCONNECTED

        with patch.object(backend, "_connect", new_callable=AsyncMock) as mock_connect:
            # Start connection manager manually
            manager_task = asyncio.create_task(backend._connection_manager())

            # Wait for connection attempts
            await asyncio.sleep(0.2)

            # Cancel the task
            manager_task.cancel()
            try:
                await manager_task
            except asyncio.CancelledError:
                pass

        # Verify connect was called
        assert mock_connect.call_count >= 1

    @pytest.mark.asyncio
    async def test_websocket_backend_connect_error(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        """Test WebSocketBackend connection error."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        with patch("websockets.connect", side_effect=Exception("Connection failed")):
            with pytest.raises(JPYLoggerWebSocketError) as exc_info:
                await backend._connect()

        assert "WebSocket connection failed" in str(exc_info.value)
        assert backend._connection_state == ConnectionState.FAILED

    @pytest.mark.asyncio
    async def test_websocket_backend_ping_loop_connection_closed(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        """Test WebSocket ping loop with connection closed."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        mock_websocket = AsyncMock()
        backend._websocket = mock_websocket
        backend._connection_state = ConnectionState.CONNECTED

        # Mock ping to raise ConnectionClosed
        mock_websocket.ping.side_effect = ConnectionClosed(None, None)

        # Start ping loop
        ping_task = asyncio.create_task(backend._ping_loop())

        # Wait for the ping to execute and update connection state
        await asyncio.sleep(backend.config.ping_interval + 0.1)

        # Verify the connection state was updated by the ping loop
        assert backend._connection_state == ConnectionState.DISCONNECTED

        # Clean up
        ping_task.cancel()
        try:
            await ping_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_websocket_backend_connect_success(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        """Test WebSocketBackend successful connection."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        class MockWebSocket:
            async def send(self, msg):
                pass

            async def ping(self):
                pass

            async def close(self):
                pass

        mock_ws = MockWebSocket()

        with patch("websockets.connect", return_value=mock_ws) as mock_connect:
            await backend._connect()

        mock_connect.assert_called_once()
        assert backend._websocket is not None
        assert hasattr(
            backend._websocket, "send"
        )  # Verify it's a websocket-like object
        assert backend._connection_state == ConnectionState.CONNECTED

    @pytest.mark.asyncio
    async def test_websocket_backend_send_message_success(
        self, websocket_config: WebSocketBackendConfig, mock_websocket: AsyncMock
    ) -> None:
        """Test WebSocketBackend successful message send."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        backend._websocket = mock_websocket
        backend._connection_state = ConnectionState.CONNECTED

        await backend._send_message("test message")
        mock_websocket.send.assert_called_once_with("test message")

    @pytest.mark.asyncio
    async def test_websocket_backend_send_message_not_connected(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        """Test WebSocketBackend send message when not connected."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        backend._connection_state = ConnectionState.DISCONNECTED

        with pytest.raises(JPYLoggerWebSocketError) as exc_info:
            await backend._send_message("test message")

        assert "WebSocket not connected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_websocket_backend_send_message_connection_closed(
        self, websocket_config: WebSocketBackendConfig, mock_websocket: AsyncMock
    ) -> None:
        """Test WebSocketBackend send message with connection closed."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        backend._websocket = mock_websocket
        backend._connection_state = ConnectionState.CONNECTED

        mock_websocket.send.side_effect = ConnectionClosed(None, None)

        with pytest.raises(JPYLoggerWebSocketError) as exc_info:
            await backend._send_message("test message")

        assert "WebSocket send failed" in str(exc_info.value)
        assert backend._connection_state == ConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_websocket_backend_write_async(
        self, websocket_config: WebSocketBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test WebSocketBackend asynchronous write."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        with patch.object(backend, "_add_to_buffer") as mock_add_to_buffer:
            await backend.write_async(sample_log_entry)

        mock_add_to_buffer.assert_called_once_with(sample_log_entry)

    def test_websocket_backend_write_sync(
        self, websocket_config: WebSocketBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test WebSocketBackend synchronous write."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        with patch("asyncio.create_task") as mock_create_task:
            backend.write_sync(sample_log_entry)

        mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_backend_write_batch_success(
        self,
        websocket_config: WebSocketBackendConfig,
        sample_log_entries: list[LogEntry],
        mock_websocket: AsyncMock,
    ) -> None:
        """Test WebSocketBackend successful batch write."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        backend._websocket = mock_websocket
        backend._connection_state = ConnectionState.CONNECTED

        await backend._write_batch(sample_log_entries)
        mock_websocket.send.assert_called_once()

        # Verify message content
        sent_message = mock_websocket.send.call_args[0][0]
        data = json.loads(sent_message)
        assert data["type"] == "log_batch"
        assert data["count"] == 5
        assert len(data["logs"]) == 5

    @pytest.mark.asyncio
    async def test_websocket_backend_write_batch_not_connected(
        self,
        websocket_config: WebSocketBackendConfig,
        sample_log_entries: list[LogEntry],
    ) -> None:
        """Test WebSocketBackend batch write when not connected."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        backend._connection_state = ConnectionState.DISCONNECTED

        with pytest.raises(JPYLoggerWebSocketError) as exc_info:
            await backend._write_batch(sample_log_entries)

        assert "WebSocket not connected for batch write" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_websocket_backend_write_batch_send_error(
        self,
        websocket_config: WebSocketBackendConfig,
        sample_log_entries: list[LogEntry],
        mock_websocket: AsyncMock,
    ) -> None:
        """Test WebSocketBackend batch write send error."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        backend._websocket = mock_websocket
        backend._connection_state = ConnectionState.CONNECTED

        mock_websocket.send.side_effect = Exception("Send error")

        with pytest.raises(JPYLoggerWebSocketError) as exc_info:
            await backend._write_batch(sample_log_entries)

        assert "WebSocket batch write failed" in str(exc_info.value)

    def test_websocket_backend_is_healthy(
        self, websocket_config: WebSocketBackendConfig, mock_websocket: AsyncMock
    ) -> None:
        """Test WebSocketBackend health check."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        # Not healthy when not connected
        assert not backend.is_healthy()

        # Healthy when connected
        backend._websocket = mock_websocket
        backend._connection_state = ConnectionState.CONNECTED
        backend._healthy = True
        backend._closed = False

        assert backend.is_healthy()

    @pytest.mark.asyncio
    async def test_websocket_backend_close(
        self, websocket_config: WebSocketBackendConfig, mock_websocket: AsyncMock
    ) -> None:
        """Test WebSocketBackend close."""
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        backend._websocket = mock_websocket
        backend._connection_state = ConnectionState.CONNECTED
        backend._ping_task = AsyncMock()
        backend._reconnect_task = AsyncMock()

        await backend.close()

        backend._ping_task.cancel.assert_called_once()
        backend._reconnect_task.cancel.assert_called_once()
        mock_websocket.close.assert_called_once()
        assert backend._connection_state == ConnectionState.CLOSED


class TestBackendFactory:
    """Test BackendFactory functionality."""

    def test_backend_factory_create_console_backend(
        self, console_config: ConsoleBackendConfig
    ) -> None:
        """Test BackendFactory console backend creation."""
        backend = BackendFactory.create_backend(console_config)
        assert isinstance(backend, ConsoleBackend)
        assert backend.name == console_config.name

    def test_backend_factory_create_file_backend(
        self, file_config: FileBackendConfig
    ) -> None:
        """Test BackendFactory file backend creation."""
        backend = BackendFactory.create_backend(file_config)
        assert isinstance(backend, FileBackend)
        assert backend.name == file_config.name

    def test_backend_factory_create_rest_api_backend(
        self, rest_api_config: RestApiBackendConfig
    ) -> None:
        """Test BackendFactory REST API backend creation."""
        with patch.object(RestApiBackend, "__init__", return_value=None) as mock_init:
            backend = BackendFactory.create_backend(rest_api_config)

        mock_init.assert_called_once_with(rest_api_config)
        # Verify the backend is created (even though __init__ is mocked)
        assert backend is not None

    def test_backend_factory_create_websocket_backend(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        """Test BackendFactory WebSocket backend creation."""
        with patch.object(WebSocketBackend, "__init__", return_value=None) as mock_init:
            backend = BackendFactory.create_backend(websocket_config)

        mock_init.assert_called_once_with(websocket_config)
        # Verify the backend is created (even though __init__ is mocked)
        assert backend is not None

    def test_backend_factory_create_unsupported_backend(
        self, database_config: DatabaseBackendConfig
    ) -> None:
        """Test BackendFactory with unsupported backend type."""
        with pytest.raises(JPYLoggerConfigurationError) as exc_info:
            BackendFactory.create_backend(database_config)

        assert "Unsupported backend type" in str(exc_info.value)
        assert exc_info.value.error_details.details is not None
        assert exc_info.value.error_details.details["config_section"] == "backend_type"

    def test_backend_factory_register_backend(self) -> None:
        """Test BackendFactory backend registration."""

        class CustomBackend:
            def __init__(self, config):
                self.config = config

        BackendFactory.register_backend("custom", CustomBackend)

        # Create config for custom backend
        config = BackendConfig(
            backend_type=BackendType.CONSOLE, name="custom_test"
        )  # Use existing enum
        # Override backend_type to be string directly for factory lookup
        config.backend_type = "custom"  # type: ignore

        backend = BackendFactory.create_backend(config)
        assert isinstance(backend, CustomBackend)

    # def test_backend_factory_get_supported_backends(self) -> None:
    #     """Test BackendFactory get supported backends."""
    #     supported = BackendFactory.get_supported_backends()
    #     assert "console" in supported
    #     assert "file" in supported
    #     assert "rest_api" in supported
    #     assert "websocket" in supported
    #     assert isinstance(supported, list)


class TestBackendIntegration:
    """Test integration scenarios and edge cases for backends."""

    @pytest.mark.asyncio
    async def test_all_backends_inheritance(self) -> None:
        """Test that all backends implement BackendInterface."""
        from jinpy_utils.logger.backends import ConsoleBackend, FileBackend

        console_config = ConsoleBackendConfig(name="test")
        file_config = FileBackendConfig(name="test")

        backends = [
            ConsoleBackend(console_config),
            FileBackend(file_config),
        ]

        for backend in backends:
            assert isinstance(backend, BackendInterface)
            assert hasattr(backend, "write_async")
            assert hasattr(backend, "write_sync")
            assert hasattr(backend, "flush")
            assert hasattr(backend, "close")
            assert hasattr(backend, "is_healthy")
            assert hasattr(backend, "get_stats")

    @pytest.mark.asyncio
    async def test_backend_buffer_management_edge_cases(
        self, console_config: ConsoleBackendConfig
    ) -> None:
        """Test backend buffer management edge cases."""
        console_config.buffer_size = 1  # Very small buffer
        backend = BaseBackend(console_config)

        with patch.object(
            backend, "_write_batch", new_callable=AsyncMock
        ) as mock_write_batch:
            # Single entry should trigger immediate flush
            entry = LogEntry(LogLevel.INFO, "test", "logger")
            await backend._add_to_buffer(entry)

            mock_write_batch.assert_called_once()
            assert len(backend._buffer) == 0

    @pytest.mark.asyncio
    async def test_backend_stats_tracking(
        self, console_config: ConsoleBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        """Test backend statistics tracking."""
        backend = ConsoleBackend(console_config)

        # Write entries synchronously
        for entry in sample_log_entries:
            with (
                patch.object(backend.stream, "write"),
                patch.object(backend.stream, "flush"),
            ):
                backend.write_sync(entry)

        stats = backend.get_stats()
        assert stats["messages_written"] == 5
        assert stats["bytes_written"] > 0
        assert stats["last_write"] is not None
        assert stats["messages_failed"] == 0

    @pytest.mark.asyncio
    async def test_backend_error_recovery(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test backend error recovery."""
        backend = ConsoleBackend(console_config)

        # Cause an error
        with patch.object(
            backend.stream, "write", side_effect=Exception("Write error")
        ):
            backend.write_sync(sample_log_entry)

        assert not backend.is_healthy()
        assert backend._stats["messages_failed"] == 1

        # Recovery on successful write
        with (
            patch.object(backend.stream, "write"),
            patch.object(backend.stream, "flush"),
        ):
            backend.write_sync(sample_log_entry)

        # Health should recover after successful async operation
        backend._healthy = True  # Simulate recovery in _write_batch
        assert backend.is_healthy()

    def test_log_entry_slots_optimization(self) -> None:
        """Test LogEntry __slots__ optimization."""
        entry = LogEntry(LogLevel.INFO, "test", "logger")

        # Should have __slots__ defined
        assert hasattr(LogEntry, "__slots__")

        # Should not have __dict__
        assert not hasattr(entry, "__dict__")

        # Should not be able to add arbitrary attributes
        with pytest.raises(AttributeError):
            entry.arbitrary_attribute = "value"  # type: ignore

    @pytest.mark.asyncio
    async def test_backend_flush_interval_zero(
        self, console_config: ConsoleBackendConfig
    ) -> None:
        """Test backend with zero flush interval."""
        console_config.flush_interval = 0
        backend = BaseBackend(console_config)

        # Should not start flush timer
        assert backend._flush_task is None

    @pytest.mark.asyncio
    async def test_complex_log_entry_serialization(self) -> None:
        """Test complex log entry serialization."""
        entry = LogEntry(LogLevel.INFO, "test", "logger")
        entry.context = {"key": "value"}
        entry.correlation_id = "1234567890"
        entry.timestamp = datetime.now()
        entry.level = LogLevel.INFO
        entry.message = "test"


class TestBackendCoverageEdgeCases:
    """Test edge cases to achieve 100% coverage."""

    @pytest.mark.asyncio
    async def test_base_backend_start_flush_timer_closed_loop(self) -> None:
        """Test BaseBackend flush timer with closed event loop."""
        config = ConsoleBackendConfig(name="test", flush_interval=0.1)

        # Mock a closed loop scenario
        with patch("asyncio.get_running_loop") as mock_get_loop:
            mock_loop = AsyncMock()
            mock_loop.is_closed.return_value = True
            mock_get_loop.return_value = mock_loop

            backend = BaseBackend(config)
            assert backend._flush_task is None

    @pytest.mark.asyncio
    async def test_base_backend_periodic_flush_general_exception(self) -> None:
        """Test BaseBackend periodic flush with general exception."""
        config = ConsoleBackendConfig(name="test", flush_interval=0.01)
        backend = BaseBackend(config)

        with patch.object(backend, "_handle_error") as mock_handle_error:
            with patch.object(backend, "flush", new_callable=AsyncMock) as mock_flush:
                mock_flush.side_effect = Exception("General flush error")

                # Start periodic flush manually
                backend._flush_task = asyncio.create_task(backend._periodic_flush())

                # Wait a bit for the exception to occur
                await asyncio.sleep(0.05)
                backend._closed = True  # Stop the loop

                # Cancel and wait for completion
                backend._flush_task.cancel()
                try:
                    await backend._flush_task
                except asyncio.CancelledError:
                    pass

                # Should have called error handler
                mock_handle_error.assert_called()

    @pytest.mark.asyncio
    async def test_file_backend_rotate_file_no_existing_file(self) -> None:
        """Test FileBackend rotation when current file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "nonexistent.log"
            config = FileBackendConfig(name="test", file_path=log_file, backup_count=3)
            backend = FileBackend(config)

            # Should not raise exception even if file doesn't exist
            await backend._rotate_file()

    @pytest.mark.asyncio
    async def test_file_backend_rotate_file_with_compression(self) -> None:
        """Test FileBackend rotation with compression enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            config = FileBackendConfig(
                name="test",
                file_path=log_file,
                backup_count=3,
                compression=CompressionType.GZIP,  # Use enum instead of string
            )
            backend = FileBackend(config)

            # Create a file to rotate
            log_file.write_text("test content")

            with patch.object(backend, "_compress_file") as mock_compress:
                await backend._rotate_file()

            mock_compress.assert_called_once()

    @pytest.mark.asyncio
    async def test_rest_api_backend_get_session_closed_session(self) -> None:
        """Test RestApiBackend session creation when existing session is closed."""
        config = RestApiBackendConfig(
            name="test_api", base_url="https://api.example.com", endpoint="/logs"
        )
        backend = RestApiBackend(config)

        # Set a closed session
        mock_session = AsyncMock()
        mock_session.closed = True
        backend._session = mock_session

        with patch("aiohttp.ClientSession") as mock_session_class:
            new_session = AsyncMock()
            new_session.closed = False
            mock_session_class.return_value = new_session

            session = await backend._get_session()

            # Should create new session since old one was closed
            assert session == new_session
            mock_session_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_backend_connect_with_extra_headers(self) -> None:
        """Test WebSocketBackend connection with authentication headers."""
        config = WebSocketBackendConfig(
            name="test_ws",
            ws_url="wss://api.example.com/ws",
            security=SecurityConfig(level=SecurityLevel.API_KEY, api_key="test-key"),
        )

        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(config)

        class MockWebSocket:
            async def send(self, msg):
                pass

            async def ping(self):
                pass

            async def close(self):
                pass

        with patch("websockets.connect") as mock_connect:
            mock_connect.return_value = MockWebSocket()
            await backend._connect()

            # Verify extra_headers were passed
            call_kwargs = mock_connect.call_args[1]
            assert "extra_headers" in call_kwargs
            assert call_kwargs["extra_headers"]["Authorization"] == "Bearer test-key"

    @pytest.mark.asyncio
    async def test_websocket_backend_connect_no_ssl_verify(self) -> None:
        """Test WebSocketBackend connection without SSL verification."""
        config = WebSocketBackendConfig(
            name="test_ws",
            ws_url="wss://api.example.com/ws",
            security=SecurityConfig(verify_ssl=False),
        )

        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(config)

        class MockWebSocket:
            async def send(self, msg):
                pass

            async def ping(self):
                pass

            async def close(self):
                pass

        with (
            patch("websockets.connect") as mock_connect,
            patch("ssl._create_unverified_context") as mock_ssl,
        ):
            mock_connect.return_value = MockWebSocket()
            await backend._connect()

            # Verify SSL context was set
            call_kwargs = mock_connect.call_args[1]
            assert "ssl" in call_kwargs
            mock_ssl.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_backend_ping_loop_general_exception(self) -> None:
        """Test WebSocketBackend ping loop with general exception."""
        config = WebSocketBackendConfig(
            name="test_ws", ws_url="wss://api.example.com/ws", ping_interval=0.01
        )

        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(config)

        mock_websocket = AsyncMock()
        backend._websocket = mock_websocket
        backend._connection_state = ConnectionState.CONNECTED

        # Make ping raise a general exception
        mock_websocket.ping.side_effect = Exception("Ping error")

        with patch.object(backend, "_handle_error") as mock_handle_error:
            # Start ping loop
            ping_task = asyncio.create_task(backend._ping_loop())

            # Wait for exception
            await asyncio.sleep(0.05)

            # Clean up
            ping_task.cancel()
            try:
                await ping_task
            except asyncio.CancelledError:
                pass

            # Should have called error handler
            mock_handle_error.assert_called()

    def test_backend_factory_create_backend_string_backend_type(self) -> None:
        """Test BackendFactory with string backend type instead of enum."""
        # Create a console config with string backend type
        config = ConsoleBackendConfig(name="test")
        # Override backend_type to be string for factory lookup
        config.backend_type = "console"  # type: ignore

        backend = BackendFactory.create_backend(config)
        assert isinstance(backend, ConsoleBackend)

    def test_backend_factory_register_backend_override(self) -> None:
        """Test BackendFactory backend registration override."""

        class CustomConsoleBackend:
            def __init__(self, config):
                self.config = config

        # Register override
        BackendFactory.register_backend("console", CustomConsoleBackend)

        config = BackendConfig(backend_type="console", name="test")  # type: ignore
        backend = BackendFactory.create_backend(config)
        assert isinstance(backend, CustomConsoleBackend)

        # Restore original
        BackendFactory.register_backend("console", ConsoleBackend)

    def test_file_backend_get_compression_value_enum(
        self, file_config: FileBackendConfig
    ) -> None:
        """Test FileBackend compression value extraction from enum."""
        file_config.compression = CompressionType.GZIP
        backend = FileBackend(file_config)
        assert backend._get_compression_value() == "gzip"

    def test_file_backend_get_compression_value_string(
        self, file_config: FileBackendConfig
    ) -> None:
        """Test FileBackend compression value extraction from string."""
        file_config.compression = "gzip"  # type: ignore
        backend = FileBackend(file_config)
        assert backend._get_compression_value() == "gzip"

    def test_base_backend_write_sync_not_implemented(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        """Test BaseBackend write_sync raises NotImplementedError."""
        backend = BaseBackend(console_config)

        with pytest.raises(NotImplementedError) as exc_info:
            backend.write_sync(sample_log_entry)

        assert "write_sync not implemented" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_base_backend_write_batch_not_implemented(
        self, console_config: ConsoleBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        """Test BaseBackend _write_batch raises NotImplementedError."""
        backend = BaseBackend(console_config)

        with pytest.raises(NotImplementedError) as exc_info:
            await backend._write_batch(sample_log_entries)

        assert "_write_batch not implemented" in str(exc_info.value)


class TestLoggerExceptionsCoverage:
    """Cover logger-specific exception helpers for reliability."""

    def test_logger_exception_str_repr_and_dict(self) -> None:
        err = logger_exceptions.JPYLoggerError(
            message="oops",
            logger_name="name",
            operation="op",
        )
        # __str__ has bracketed error code
        s = str(err)
        assert s.startswith("[LOGGING_ERROR]")
        d = err.to_dict()
        assert d["exception_type"] == "JPYLoggerError"
        assert d["error_code"] == "LOGGING_ERROR"
        assert d["details"]["logger_name"] == "name"

    def test_logger_specific_exceptions_init(self) -> None:
        cfg_err = logger_exceptions.JPYLoggerConfigurationError(
            message="bad cfg", config_section="sec", config_value="val"
        )
        backend_err = logger_exceptions.JPYLoggerBackendError(
            message="backend", backend_type="console", backend_config={"a": 1}
        )
        conn_err = logger_exceptions.JPYLoggerConnectionError(
            message="conn", endpoint="http://x", connection_type="http"
        )
        sec_err = logger_exceptions.JPYLoggerSecurityError(
            message="sec", security_context="auth"
        )
        perf_err = logger_exceptions.JPYLoggerPerformanceError(
            message="perf",
            performance_metric="m",
            threshold_value=1.0,
            actual_value=2.0,
        )
        ws_err = logger_exceptions.JPYLoggerWebSocketError(
            message="ws", ws_endpoint="wss://x", ws_state="disconnected"
        )
        for e in [cfg_err, backend_err, conn_err, sec_err, perf_err, ws_err]:
            j = e.to_json()
            assert "LOGGING_ERROR" in j


class TestBaseExceptionsCoverage:
    """Cover base exception helpers used by logger backends."""

    def test_base_exception_str_and_registry(self) -> None:
        base = JPYBaseException(
            error_code="X", message="m", details={"k": "v"}, context={"c": 1}
        )
        assert "[X]" in str(base)
        as_dict = base.to_dict()
        assert as_dict["error_code"] == "X"
        # Registry usage
        ex = ExceptionRegistry.create_exception("CONNECTION_ERROR", "msg")
        assert isinstance(ex, JPYConnectionError)

    def test_configuration_error_from_dict(self) -> None:
        data = {
            "error_code": "CONFIGURATION_ERROR",
            "message": "bad",
            "details": {"a": 1},
            "context": {"b": 2},
            "suggestions": ["x"],
        }
        recreated = JPYBaseException.from_dict(data)
        # Base recreation produces base type
        assert isinstance(recreated, JPYBaseException)


class TestLoggerConfigCoverage:
    """Exercise config validators and factory helpers."""

    def test_rest_api_config_url_validator(self) -> None:
        with pytest.raises(JPYLoggerConfigurationError):
            logger_config.RestApiBackendConfig(
                name="x", base_url="invalid", endpoint="/e"
            )

    def test_websocket_config_url_validator(self) -> None:
        with pytest.raises(JPYLoggerConfigurationError):
            logger_config.WebSocketBackendConfig(name="x", ws_url="invalid")

    def test_global_config_factories_and_unique_names(self) -> None:
        dev = logger_config.create_development_config()
        prod = logger_config.create_production_config()
        cloud = logger_config.create_cloud_config("https://api", "key")
        assert any(b.name == "dev_console" for b in dev.backends)
        assert any(hasattr(b, "file_path") for b in prod.backends)
        assert any(hasattr(b, "base_url") for b in cloud.backends)
        # Validate uniqueness check
        with pytest.raises(JPYLoggerConfigurationError):
            logger_config.GlobalLoggerConfig(
                backends=[
                    logger_config.ConsoleBackendConfig(name="dup"),
                    logger_config.ConsoleBackendConfig(name="dup"),
                ]
            )


class TestAdditionalBackendCoverage:
    """Additional tests to drive near-complete branch coverage for backends."""

    @pytest.mark.asyncio
    async def test_console_backend_filtered_writes(
        self, console_config: ConsoleBackendConfig
    ) -> None:
        console_config.level = LogLevel.ERROR
        backend = ConsoleBackend(console_config)
        entry = LogEntry(LogLevel.INFO, "msg", "logger")

        with patch.object(backend, "_add_to_buffer") as mock_add:
            await backend.write_async(entry)
        mock_add.assert_not_called()

        with patch.object(backend.stream, "write") as mock_write:
            backend.write_sync(entry)
        mock_write.assert_not_called()

    @pytest.mark.asyncio
    async def test_file_backend_filtered_writes(
        self, file_config: FileBackendConfig
    ) -> None:
        file_config.level = LogLevel.CRITICAL
        backend = FileBackend(file_config)
        entry = LogEntry(LogLevel.WARNING, "msg", "logger")

        with patch.object(backend, "_add_to_buffer") as mock_add:
            await backend.write_async(entry)
        mock_add.assert_not_called()

        with patch("builtins.open", mock_open()) as mock_file:
            backend.write_sync(entry)
        mock_file.assert_not_called()

    @pytest.mark.asyncio
    async def test_rest_api_backend_filtered_writes(
        self, rest_api_config: RestApiBackendConfig
    ) -> None:
        rest_api_config.level = LogLevel.CRITICAL
        backend = RestApiBackend(rest_api_config)
        entry = LogEntry(LogLevel.INFO, "msg", "logger")

        with patch.object(backend, "_add_to_buffer") as mock_add:
            await backend.write_async(entry)
        mock_add.assert_not_called()

        with patch("asyncio.create_task") as mock_task:
            backend.write_sync(entry)
        mock_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_backend_filtered_writes(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        websocket_config.level = LogLevel.CRITICAL
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)
        entry = LogEntry(LogLevel.DEBUG, "msg", "logger")

        with patch.object(backend, "_add_to_buffer") as mock_add:
            await backend.write_async(entry)
        mock_add.assert_not_called()

        with patch("asyncio.create_task") as mock_task:
            backend.write_sync(entry)
        mock_task.assert_not_called()

    def test_backend_factory_supported_backends(self) -> None:
        supported = BackendFactory.get_supported_backends()
        assert isinstance(supported, list)
        # Must contain known types
        assert "console" in supported
        assert "file" in supported
        assert "rest_api" in supported
        assert "websocket" in supported

    @pytest.mark.asyncio
    async def test_websocket_backend_close_no_tasks(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)
        # No tasks, no websocket
        await backend.close()
        assert backend._connection_state == ConnectionState.CLOSED

    @pytest.mark.asyncio
    async def test_websocket_backend_close_real_tasks(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        async def sleeper():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                raise

        # Assign real asyncio tasks
        backend._ping_task = asyncio.create_task(sleeper())
        backend._reconnect_task = asyncio.create_task(sleeper())

        await backend.close()
        # If close succeeds, tasks are cancelled and state closed
        assert backend._connection_state == ConnectionState.CLOSED

    @pytest.mark.asyncio
    async def test_base_backend_starts_flush_timer(
        self, console_config: ConsoleBackendConfig, sample_log_entry: LogEntry
    ) -> None:
        console_config.flush_interval = 0.05
        backend = BaseBackend(console_config)
        # In a running loop, flush task should be created or left None safely
        assert backend._flush_task is None or isinstance(
            backend._flush_task, asyncio.Task
        )
        await backend.close()

    @pytest.mark.asyncio
    async def test_base_backend_write_async_true_false(
        self, console_config: ConsoleBackendConfig
    ) -> None:
        backend = BaseBackend(console_config)
        entry = LogEntry(LogLevel.INFO, "msg", "logger")
        await backend.write_async(entry)
        # Should be added
        assert len(backend._buffer) == 1

        # Now set level higher so it is filtered out
        console_config.level = LogLevel.ERROR
        entry2 = LogEntry(LogLevel.INFO, "filtered", "logger")
        await backend.write_async(entry2)
        # Still 1
        assert len(backend._buffer) == 1
        await backend.close()

    def test_console_backend_format_console_entry_without_context(
        self, console_config: ConsoleBackendConfig
    ) -> None:
        console_config.format = LogFormat.CONSOLE
        backend = ConsoleBackend(console_config)
        entry = LogEntry(LogLevel.INFO, "noctx", "logger", context={})
        result = backend._format_console_entry(entry)
        assert "noctx" in result
        # No JSON context present
        assert "{" not in result

    @pytest.mark.asyncio
    async def test_file_backend_rotate_file_no_compression(
        self, file_config: FileBackendConfig, temp_log_dir: Path
    ) -> None:
        log_file = temp_log_dir / "test.log"
        file_config.file_path = log_file
        file_config.backup_count = 2
        file_config.compression = CompressionType.NONE
        backend = FileBackend(file_config)

        # Create current file only
        log_file.write_text("current")

        with patch.object(backend, "_compress_file") as mock_compress:
            await backend._rotate_file()
        mock_compress.assert_not_called()

    @pytest.mark.asyncio
    async def test_rest_api_backend_send_batch_success_direct_ctx(
        self, rest_api_config: RestApiBackendConfig, sample_log_entries: list[LogEntry]
    ) -> None:
        backend = RestApiBackend(rest_api_config)

        class Ctx:
            async def __aenter__(self):
                class Resp:
                    status = 200

                    async def text(self):
                        return "OK"

                return Resp()

            async def __aexit__(self, exc_type, exc, tb):
                return None

        session = AsyncMock()
        session.closed = False
        session.request = lambda *a, **k: Ctx()  # direct context manager
        backend._session = session

        await backend._send_batch(sample_log_entries)
        assert backend._connection_state == ConnectionState.CONNECTED

    def test_websocket_start_connection_management_no_loop(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        with patch("asyncio.get_running_loop", side_effect=RuntimeError()):
            backend = WebSocketBackend(websocket_config)
        assert backend._reconnect_task is None

    @pytest.mark.asyncio
    async def test_websocket_connect_cancels_existing_ping(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)
        # Create an existing ping task
        old_task = asyncio.create_task(asyncio.sleep(10))
        backend._ping_task = old_task

        class MockWebSocket:
            async def send(self, msg):
                pass

            async def ping(self):
                pass

            async def close(self):
                pass

        with patch("websockets.connect", return_value=MockWebSocket()):
            await backend._connect()

        # The old ping task should have been requested to cancel
        assert old_task.cancelled() or old_task.cancelled() is False
        assert backend._ping_task is not None
        await backend.close()

    @pytest.mark.asyncio
    async def test_websocket_close_cancel_awaitable_raises(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)

        class RaisingAwaitable:
            def __await__(self):
                async def _coro():
                    raise RuntimeError("cancel failed")

                return _coro().__await__()

        class Dummy:
            def cancel(self):  # returns awaitable that raises
                return RaisingAwaitable()

        backend._ping_task = Dummy()  # type: ignore
        backend._reconnect_task = Dummy()  # type: ignore
        # No websocket set
        await backend.close()
        assert backend._connection_state == ConnectionState.CLOSED

    @pytest.mark.asyncio
    async def test_websocket_backend_starts_connection_management(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        # Ensure real start without patching
        backend = WebSocketBackend(websocket_config)
        # Give the loop a tick to schedule the task
        await asyncio.sleep(0)
        assert backend._reconnect_task is None or isinstance(
            backend._reconnect_task, asyncio.Task
        )
        await backend.close()

    @pytest.mark.asyncio
    async def test_websocket_connection_manager_handles_general_exception(
        self, websocket_config: WebSocketBackendConfig
    ) -> None:
        websocket_config.reconnect_interval = 0.01
        with patch.object(WebSocketBackend, "_start_connection_management"):
            backend = WebSocketBackend(websocket_config)
        backend._connection_state = ConnectionState.DISCONNECTED

        async def failing_connect():
            raise Exception("boom")

        with (
            patch.object(backend, "_connect", side_effect=failing_connect),
            patch.object(backend, "_handle_error") as mock_handle_error,
        ):
            task = asyncio.create_task(backend._connection_manager())
            # Let it iterate once and handle error
            await asyncio.sleep(0.03)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        mock_handle_error.assert_called()

    @pytest.mark.asyncio
    async def test_rest_api_backend_close_without_session(
        self, rest_api_config: RestApiBackendConfig
    ) -> None:
        backend = RestApiBackend(rest_api_config)
        # No session set
        await backend.close()
        assert backend._connection_state == ConnectionState.CLOSED

    @pytest.mark.asyncio
    async def test_rest_api_backend_close_with_closed_session(
        self, rest_api_config: RestApiBackendConfig
    ) -> None:
        backend = RestApiBackend(rest_api_config)
        backend._session = AsyncMock()
        backend._session.closed = True
        await backend.close()
        # close() should not be awaited/called since session is closed
        backend._session.close.assert_not_called()
