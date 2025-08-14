"""Tests for logger enums to reach 100% coverage."""

from jinpy_utils.logger.enums import (
    BackendType,
    BatchStrategy,
    CompressionType,
    ConnectionState,
    LogFormat,
    LogLevel,
    RetryStrategy,
    SecurityLevel,
)


class TestLogLevelComparisons:
    def test_numeric_value_mapping(self) -> None:
        assert LogLevel.TRACE.numeric_value == 5
        assert LogLevel.DEBUG.numeric_value == 10
        assert LogLevel.INFO.numeric_value == 20
        assert LogLevel.WARNING.numeric_value == 30
        assert LogLevel.ERROR.numeric_value == 40
        assert LogLevel.CRITICAL.numeric_value == 50

    def test_all_comparisons_true_false(self) -> None:
        # Less-than comparisons
        assert LogLevel.DEBUG < LogLevel.INFO
        assert not (LogLevel.ERROR < LogLevel.DEBUG)
        # Greater-than comparisons
        assert LogLevel.ERROR > LogLevel.WARNING
        assert not (LogLevel.DEBUG > LogLevel.ERROR)
        # Less-or-equal
        assert LogLevel.INFO <= LogLevel.INFO
        assert LogLevel.INFO <= LogLevel.WARNING
        assert not (LogLevel.ERROR <= LogLevel.DEBUG)
        # Greater-or-equal
        assert LogLevel.WARNING >= LogLevel.WARNING
        assert LogLevel.ERROR >= LogLevel.WARNING
        assert not (LogLevel.DEBUG >= LogLevel.ERROR)


class TestOtherEnums:
    def test_backend_type_members(self) -> None:
        assert BackendType.CONSOLE.value == "console"
        assert BackendType.FILE.value == "file"
        assert BackendType.ROTATING_FILE.value == "rotating_file"
        assert BackendType.REST_API.value == "rest_api"
        assert BackendType.DATABASE.value == "database"
        assert BackendType.WEBSOCKET.value == "websocket"
        assert BackendType.SYSLOG.value == "syslog"
        assert BackendType.MEMORY.value == "memory"
        assert BackendType.REDIS.value == "redis"
        assert BackendType.KAFKA.value == "kafka"
        assert BackendType.ELASTICSEARCH.value == "elasticsearch"

    def test_log_format_members(self) -> None:
        assert LogFormat.JSON.value == "json"
        assert LogFormat.CONSOLE.value == "console"
        assert LogFormat.PLAIN.value == "plain"
        assert LogFormat.STRUCTURED.value == "structured"
        assert LogFormat.CEF.value == "cef"
        assert LogFormat.GELF.value == "gelf"

    def test_compression_type_members(self) -> None:
        assert CompressionType.NONE.value == "none"
        assert CompressionType.GZIP.value == "gzip"
        assert CompressionType.BZIP2.value == "bzip2"
        assert CompressionType.XZ.value == "xz"
        assert CompressionType.ZIP.value == "zip"

    def test_security_level_members(self) -> None:
        assert SecurityLevel.NONE.value == "none"
        assert SecurityLevel.BASIC.value == "basic"
        assert SecurityLevel.TLS.value == "tls"
        assert SecurityLevel.MUTUAL_TLS.value == "mutual_tls"
        assert SecurityLevel.API_KEY.value == "api_key"
        assert SecurityLevel.OAUTH2.value == "oauth2"

    def test_connection_state_members(self) -> None:
        assert ConnectionState.DISCONNECTED.value == "disconnected"
        assert ConnectionState.CONNECTING.value == "connecting"
        assert ConnectionState.CONNECTED.value == "connected"
        assert ConnectionState.RECONNECTING.value == "reconnecting"
        assert ConnectionState.FAILED.value == "failed"
        assert ConnectionState.CLOSED.value == "closed"

    def test_batch_and_retry_strategies(self) -> None:
        assert BatchStrategy.SIZE_BASED.value == "size_based"
        assert BatchStrategy.TIME_BASED.value == "time_based"
        assert BatchStrategy.HYBRID.value == "hybrid"
        assert BatchStrategy.IMMEDIATE.value == "immediate"

        assert RetryStrategy.NONE.value == "none"
        assert RetryStrategy.LINEAR.value == "linear"
        assert RetryStrategy.EXPONENTIAL.value == "exponential"
        assert RetryStrategy.FIXED.value == "fixed"
