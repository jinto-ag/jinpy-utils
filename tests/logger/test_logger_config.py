"""Tests for logger configuration classes."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from jinpy_utils.logger.config import (
    BackendConfig,
    ConsoleBackendConfig,
    DatabaseBackendConfig,
    FileBackendConfig,
    GlobalLoggerConfig,
    LoggerConfig,
    RestApiBackendConfig,
    RetryConfig,
    SecurityConfig,
    WebSocketBackendConfig,
    create_cloud_config,
    create_development_config,
    create_production_config,
)
from jinpy_utils.logger.enums import (
    BackendType,
    BatchStrategy,
    CompressionType,
    LogFormat,
    LogLevel,
    RetryStrategy,
    SecurityLevel,
)
from jinpy_utils.logger.exceptions import JPYLoggerConfigurationError


class TestSecurityConfig:
    """Test SecurityConfig functionality."""

    def test_security_config_basic(self) -> None:
        """Test basic SecurityConfig creation."""
        config = SecurityConfig()
        assert config.level == SecurityLevel.NONE
        assert config.api_key is None
        assert config.tls_cert_path is None
        assert config.tls_key_path is None
        assert config.ca_cert_path is None
        assert config.verify_ssl is True
        assert config.oauth2_token is None

    def test_security_config_with_values(self) -> None:
        """Test SecurityConfig with all values set."""
        config = SecurityConfig(
            level=SecurityLevel.API_KEY,
            api_key="test-api-key",
            tls_cert_path=Path("/path/to/cert.pem"),
            tls_key_path=Path("/path/to/key.pem"),
            ca_cert_path=Path("/path/to/ca.pem"),
            verify_ssl=False,
            oauth2_token="oauth-token",
        )
        assert config.level == SecurityLevel.API_KEY
        assert config.api_key == "test-api-key"
        assert config.tls_cert_path == Path("/path/to/cert.pem")
        assert config.tls_key_path == Path("/path/to/key.pem")
        assert config.ca_cert_path == Path("/path/to/ca.pem")
        assert config.verify_ssl is False
        assert config.oauth2_token == "oauth-token"

    def test_security_config_environment_variable_api_key(self) -> None:
        """Test API key environment variable resolution."""
        with patch.dict(os.environ, {"TEST_API_KEY": "env-api-key"}):
            config = SecurityConfig(api_key="${TEST_API_KEY}")
            assert config.api_key == "env-api-key"

    def test_security_config_environment_variable_oauth_token(self) -> None:
        """Test OAuth token environment variable resolution."""
        with patch.dict(os.environ, {"TEST_OAUTH_TOKEN": "env-oauth-token"}):
            config = SecurityConfig(oauth2_token="${TEST_OAUTH_TOKEN}")
            assert config.oauth2_token == "env-oauth-token"

    def test_security_config_environment_variable_missing(self) -> None:
        """Test environment variable that doesn't exist."""
        config = SecurityConfig(api_key="${NON_EXISTENT_KEY}")
        assert config.api_key is None

    def test_security_config_non_environment_variable(self) -> None:
        """Test non-environment variable values pass through unchanged."""
        config = SecurityConfig(
            api_key="direct-api-key",
            oauth2_token="direct-oauth-token",
        )
        assert config.api_key == "direct-api-key"
        assert config.oauth2_token == "direct-oauth-token"

    def test_security_config_json_serialization(self) -> None:
        """Test JSON serialization of SecurityConfig."""
        config = SecurityConfig(
            level=SecurityLevel.TLS,
            api_key="test-key",
            verify_ssl=False,
        )
        json_str = config.model_dump_json()
        data = json.loads(json_str)
        assert data["level"] == "tls"
        assert data["api_key"] == "test-key"
        assert data["verify_ssl"] is False


class TestRetryConfig:
    """Test RetryConfig functionality."""

    def test_retry_config_basic(self) -> None:
        """Test basic RetryConfig creation."""
        config = RetryConfig()
        assert config.strategy == RetryStrategy.EXPONENTIAL
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_multiplier == 2.0
        assert config.jitter is True

    def test_retry_config_with_values(self) -> None:
        """Test RetryConfig with custom values."""
        config = RetryConfig(
            strategy=RetryStrategy.LINEAR,
            max_attempts=5,
            base_delay=2.0,
            max_delay=120.0,
            backoff_multiplier=1.5,
            jitter=False,
        )
        assert config.strategy == RetryStrategy.LINEAR
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.backoff_multiplier == 1.5
        assert config.jitter is False

    def test_retry_config_validation_max_attempts_min(self) -> None:
        """Test max_attempts minimum validation."""
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=0)

    def test_retry_config_validation_max_attempts_max(self) -> None:
        """Test max_attempts maximum validation."""
        with pytest.raises(ValidationError):
            RetryConfig(max_attempts=11)

    def test_retry_config_validation_base_delay_positive(self) -> None:
        """Test base_delay must be positive."""
        with pytest.raises(ValidationError):
            RetryConfig(base_delay=0.0)

    def test_retry_config_validation_max_delay_positive(self) -> None:
        """Test max_delay must be positive."""
        with pytest.raises(ValidationError):
            RetryConfig(max_delay=0.0)

    def test_retry_config_validation_backoff_multiplier_gt_one(self) -> None:
        """Test backoff_multiplier must be greater than 1."""
        with pytest.raises(ValidationError):
            RetryConfig(backoff_multiplier=1.0)

    def test_retry_config_edge_case_values(self) -> None:
        """Test edge case valid values."""
        config = RetryConfig(
            max_attempts=1,
            base_delay=0.1,
            max_delay=0.1,
            backoff_multiplier=1.1,
        )
        assert config.max_attempts == 1
        assert config.base_delay == 0.1
        assert config.max_delay == 0.1
        assert config.backoff_multiplier == 1.1


class TestBackendConfig:
    """Test BackendConfig base class functionality."""

    def test_backend_config_creation(self) -> None:
        """Test basic BackendConfig creation."""
        config = BackendConfig(
            backend_type=BackendType.CONSOLE,
            name="test-backend",
        )
        assert config.backend_type == BackendType.CONSOLE
        assert config.name == "test-backend"
        assert config.level == LogLevel.INFO
        assert config.format == LogFormat.JSON
        assert config.enabled is True
        assert isinstance(config.security, SecurityConfig)
        assert isinstance(config.retry, RetryConfig)
        assert config.buffer_size == 1000
        assert config.flush_interval == 5.0
        assert config.timeout == 30.0

    def test_backend_config_with_custom_values(self) -> None:
        """Test BackendConfig with custom values."""
        security = SecurityConfig(level=SecurityLevel.API_KEY)
        retry = RetryConfig(max_attempts=5)

        config = BackendConfig(
            backend_type=BackendType.FILE,
            name="custom-backend",
            level=LogLevel.DEBUG,
            format=LogFormat.CONSOLE,
            enabled=False,
            security=security,
            retry=retry,
            buffer_size=2000,
            flush_interval=10.0,
            timeout=60.0,
        )
        assert config.backend_type == BackendType.FILE
        assert config.name == "custom-backend"
        assert config.level == LogLevel.DEBUG
        assert config.format == LogFormat.CONSOLE
        assert config.enabled is False
        assert config.security == security
        assert config.retry == retry
        assert config.buffer_size == 2000
        assert config.flush_interval == 10.0
        assert config.timeout == 60.0

    def test_backend_config_validation_buffer_size_positive(self) -> None:
        """Test buffer_size must be positive."""
        with pytest.raises(ValidationError):
            BackendConfig(
                backend_type=BackendType.CONSOLE,
                name="test",
                buffer_size=0,
            )

    def test_backend_config_validation_flush_interval_positive(self) -> None:
        """Test flush_interval must be positive."""
        with pytest.raises(ValidationError):
            BackendConfig(
                backend_type=BackendType.CONSOLE,
                name="test",
                flush_interval=0.0,
            )

    def test_backend_config_validation_timeout_positive(self) -> None:
        """Test timeout must be positive."""
        with pytest.raises(ValidationError):
            BackendConfig(
                backend_type=BackendType.CONSOLE,
                name="test",
                timeout=0.0,
            )

    def test_backend_config_extra_fields_allowed(self) -> None:
        """Test that extra fields are allowed."""
        config = BackendConfig(
            backend_type=BackendType.CONSOLE,
            name="test",
            custom_field="custom_value",  # type: ignore
        )
        # Pydantic v2 stores extra on model attributes dynamically but may not reflect in __dict__
        assert getattr(config, "custom_field", None) == "custom_value"


class TestConsoleBackendConfig:
    """Test ConsoleBackendConfig functionality."""

    def test_console_backend_config_basic(self) -> None:
        """Test basic ConsoleBackendConfig creation."""
        config = ConsoleBackendConfig(name="console")
        assert config.backend_type == BackendType.CONSOLE
        assert config.format == LogFormat.CONSOLE
        assert config.colors is True
        assert config.stream == "stdout"

    def test_console_backend_config_with_values(self) -> None:
        """Test ConsoleBackendConfig with custom values."""
        config = ConsoleBackendConfig(
            name="console-stderr",
            colors=False,
            stream="stderr",
        )
        assert config.colors is False
        assert config.stream == "stderr"

    def test_console_backend_config_stream_validation_valid(self) -> None:
        """Test valid stream values."""
        config_stdout = ConsoleBackendConfig(name="test", stream="stdout")
        config_stderr = ConsoleBackendConfig(name="test", stream="stderr")
        assert config_stdout.stream == "stdout"
        assert config_stderr.stream == "stderr"

    def test_console_backend_config_stream_validation_invalid(self) -> None:
        """Test invalid stream value."""
        with pytest.raises(ValidationError):
            ConsoleBackendConfig(name="test", stream="invalid")


class TestFileBackendConfig:
    """Test FileBackendConfig functionality."""

    def test_file_backend_config_basic(self) -> None:
        """Test basic FileBackendConfig creation."""
        config = FileBackendConfig(name="file")
        assert config.backend_type == BackendType.FILE
        assert config.file_path == Path("logs/app.log")
        assert config.max_size_mb == 100
        assert config.backup_count == 5
        assert config.compression == CompressionType.GZIP
        assert config.encoding == "utf-8"

    def test_file_backend_config_with_values(self) -> None:
        """Test FileBackendConfig with custom values."""
        custom_path = Path("/var/log/custom.log")
        config = FileBackendConfig(
            name="custom-file",
            file_path=custom_path,
            max_size_mb=200,
            backup_count=10,
            compression=CompressionType.ZIP,
            encoding="latin-1",
        )
        assert config.file_path == custom_path
        assert config.max_size_mb == 200
        assert config.backup_count == 10
        assert config.compression == CompressionType.ZIP
        assert config.encoding == "latin-1"

    def test_file_backend_config_directory_creation(self) -> None:
        """Test that log directory is created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "nested" / "logs" / "app.log"
            config = FileBackendConfig(name="test", file_path=log_path)
            assert config.file_path.parent.exists()

    def test_file_backend_config_max_size_validation(self) -> None:
        """Test max_size_mb validation."""
        with pytest.raises(ValidationError):
            FileBackendConfig(name="test", max_size_mb=0)

    def test_file_backend_config_backup_count_validation(self) -> None:
        """Test backup_count validation allows zero."""
        config = FileBackendConfig(name="test", backup_count=0)
        assert config.backup_count == 0

    def test_file_backend_config_backup_count_negative_invalid(self) -> None:
        """Test negative backup_count is invalid."""
        with pytest.raises(ValidationError):
            FileBackendConfig(name="test", backup_count=-1)


class TestRestApiBackendConfig:
    """Test RestApiBackendConfig functionality."""

    def test_rest_api_backend_config_basic(self) -> None:
        """Test basic RestApiBackendConfig creation."""
        config = RestApiBackendConfig(
            name="api",
            base_url="https://api.example.com",
        )
        assert config.backend_type == BackendType.REST_API
        assert config.base_url == "https://api.example.com"
        assert config.endpoint == "/logs"
        assert config.method == "POST"
        assert config.headers == {}
        assert config.batch_strategy == BatchStrategy.HYBRID

    def test_rest_api_backend_config_with_values(self) -> None:
        """Test RestApiBackendConfig with custom values."""
        headers = {"Authorization": "Bearer token"}
        config = RestApiBackendConfig(
            name="custom-api",
            base_url="http://localhost:8080/",
            endpoint="/api/v1/logs",
            method="PUT",
            headers=headers,
            batch_strategy=BatchStrategy.SIZE_BASED,
        )
        assert config.base_url == "http://localhost:8080"
        assert config.endpoint == "/api/v1/logs"
        assert config.method == "PUT"
        assert config.headers == headers
        assert config.batch_strategy == BatchStrategy.SIZE_BASED

    def test_rest_api_backend_config_url_validation_https(self) -> None:
        """Test HTTPS URL validation."""
        config = RestApiBackendConfig(
            name="test",
            base_url="https://api.example.com",
        )
        assert config.base_url == "https://api.example.com"

    def test_rest_api_backend_config_url_validation_http(self) -> None:
        """Test HTTP URL validation."""
        config = RestApiBackendConfig(
            name="test",
            base_url="http://api.example.com",
        )
        assert config.base_url == "http://api.example.com"

    def test_rest_api_backend_config_url_validation_trailing_slash(self) -> None:
        """Test URL with trailing slash is stripped."""
        config = RestApiBackendConfig(
            name="test",
            base_url="https://api.example.com/",
        )
        assert config.base_url == "https://api.example.com"

    def test_rest_api_backend_config_url_validation_invalid(self) -> None:
        """Test invalid URL format."""
        with pytest.raises(JPYLoggerConfigurationError) as exc_info:
            RestApiBackendConfig(
                name="test",
                base_url="ftp://invalid.com",
            )
        assert "Invalid URL format" in str(exc_info.value)
        assert exc_info.value.error_details.details is not None
        assert exc_info.value.error_details.details["config_section"] == "base_url"
        assert (
            exc_info.value.error_details.details["config_value"] == "ftp://invalid.com"
        )

    def test_rest_api_backend_config_method_validation_valid(self) -> None:
        """Test valid HTTP methods."""
        for method in ["POST", "PUT", "PATCH"]:
            config = RestApiBackendConfig(
                name="test",
                base_url="https://api.example.com",
                method=method,
            )
            assert config.method == method

    def test_rest_api_backend_config_method_validation_invalid(self) -> None:
        """Test invalid HTTP method."""
        with pytest.raises(ValidationError):
            RestApiBackendConfig(
                name="test",
                base_url="https://api.example.com",
                method="GET",
            )


class TestWebSocketBackendConfig:
    """Test WebSocketBackendConfig functionality."""

    def test_websocket_backend_config_basic(self) -> None:
        """Test basic WebSocketBackendConfig creation."""
        config = WebSocketBackendConfig(
            name="ws",
            ws_url="wss://api.example.com/ws",
        )
        assert config.backend_type == BackendType.WEBSOCKET
        assert config.ws_url == "wss://api.example.com/ws"
        assert config.reconnect_interval == 5.0
        assert config.ping_interval == 30.0
        assert config.max_message_size == 1024 * 1024

    def test_websocket_backend_config_with_values(self) -> None:
        """Test WebSocketBackendConfig with custom values."""
        config = WebSocketBackendConfig(
            name="custom-ws",
            ws_url="ws://localhost:8080/logs",
            reconnect_interval=10.0,
            ping_interval=60.0,
            max_message_size=2048 * 1024,
        )
        assert config.ws_url == "ws://localhost:8080/logs"
        assert config.reconnect_interval == 10.0
        assert config.ping_interval == 60.0
        assert config.max_message_size == 2048 * 1024

    def test_websocket_backend_config_url_validation_wss(self) -> None:
        """Test WSS URL validation."""
        config = WebSocketBackendConfig(
            name="test",
            ws_url="wss://api.example.com/ws",
        )
        assert config.ws_url == "wss://api.example.com/ws"

    def test_websocket_backend_config_url_validation_ws(self) -> None:
        """Test WS URL validation."""
        config = WebSocketBackendConfig(
            name="test",
            ws_url="ws://api.example.com/ws",
        )
        assert config.ws_url == "ws://api.example.com/ws"

    def test_websocket_backend_config_url_validation_invalid(self) -> None:
        """Test invalid WebSocket URL format."""
        with pytest.raises(JPYLoggerConfigurationError) as exc_info:
            WebSocketBackendConfig(
                name="test",
                ws_url="https://api.example.com",
            )
        assert "Invalid WebSocket URL format" in str(exc_info.value)
        assert exc_info.value.error_details.details is not None
        assert exc_info.value.error_details.details["config_section"] == "ws_url"
        assert (
            exc_info.value.error_details.details["config_value"]
            == "https://api.example.com"
        )

    def test_websocket_backend_config_interval_validation(self) -> None:
        """Test interval validations."""
        with pytest.raises(ValidationError):
            WebSocketBackendConfig(
                name="test",
                ws_url="ws://example.com",
                reconnect_interval=0.0,
            )

        with pytest.raises(ValidationError):
            WebSocketBackendConfig(
                name="test",
                ws_url="ws://example.com",
                ping_interval=0.0,
            )

    def test_websocket_backend_config_message_size_validation(self) -> None:
        """Test max_message_size validation."""
        with pytest.raises(ValidationError):
            WebSocketBackendConfig(
                name="test",
                ws_url="ws://example.com",
                max_message_size=0,
            )


class TestDatabaseBackendConfig:
    """Test DatabaseBackendConfig functionality."""

    def test_database_backend_config_basic(self) -> None:
        """Test basic DatabaseBackendConfig creation."""
        config = DatabaseBackendConfig(
            name="db",
            connection_string="postgresql://user:pass@localhost/db",
        )
        assert config.backend_type == BackendType.DATABASE
        assert config.connection_string == "postgresql://user:pass@localhost/db"
        assert config.table_name == "logs"
        assert config.schema_name is None
        assert config.pool_size == 5
        assert config.pool_timeout == 30.0

    def test_database_backend_config_with_values(self) -> None:
        """Test DatabaseBackendConfig with custom values."""
        config = DatabaseBackendConfig(
            name="custom-db",
            connection_string="mysql://user:pass@localhost/mydb",
            table_name="application_logs",
            schema_name="logging",
            pool_size=10,
            pool_timeout=60.0,
        )
        assert config.connection_string == "mysql://user:pass@localhost/mydb"
        assert config.table_name == "application_logs"
        assert config.schema_name == "logging"
        assert config.pool_size == 10
        assert config.pool_timeout == 60.0

    def test_database_backend_config_pool_validation(self) -> None:
        """Test pool size and timeout validation."""
        with pytest.raises(ValidationError):
            DatabaseBackendConfig(
                name="test",
                connection_string="sqlite:///test.db",
                pool_size=0,
            )

        with pytest.raises(ValidationError):
            DatabaseBackendConfig(
                name="test",
                connection_string="sqlite:///test.db",
                pool_timeout=0.0,
            )


class TestGlobalLoggerConfig:
    """Test GlobalLoggerConfig functionality."""

    def test_global_logger_config_basic(self) -> None:
        """Test basic GlobalLoggerConfig creation."""
        config = GlobalLoggerConfig()
        assert config.app_name == "jinpy-utils"
        assert config.environment == "development"
        assert config.version == "1.0.0"
        assert config.default_level == LogLevel.INFO
        assert config.correlation_id_header == "X-Correlation-ID"
        assert config.enable_correlation_ids is True
        assert config.enable_structured_context is True
        assert config.max_context_size == 10000
        assert config.async_queue_size == 10000
        assert config.enable_performance_metrics is False
        assert config.enable_sanitization is True
        assert config.sensitive_fields == ["password", "token", "secret", "key", "auth"]
        assert len(config.backends) == 1
        assert isinstance(config.backends[0], ConsoleBackendConfig)
        assert config.enable_singleton is False
        assert config.singleton_name == "default"

    def test_global_logger_config_with_values(self) -> None:
        """Test GlobalLoggerConfig with custom values."""
        backends: list[
            ConsoleBackendConfig
            | FileBackendConfig
            | RestApiBackendConfig
            | WebSocketBackendConfig
            | DatabaseBackendConfig
        ] = [
            ConsoleBackendConfig(name="console"),
            FileBackendConfig(name="file"),
        ]
        sensitive_fields = ["password", "secret"]

        config = GlobalLoggerConfig(
            app_name="test-app",
            environment="production",
            version="2.0.0",
            default_level=LogLevel.WARNING,
            correlation_id_header="X-Request-ID",
            enable_correlation_ids=False,
            enable_structured_context=False,
            max_context_size=5000,
            async_queue_size=5000,
            enable_performance_metrics=True,
            enable_sanitization=False,
            sensitive_fields=sensitive_fields,
            backends=backends,
            enable_singleton=True,
            singleton_name="custom",
        )
        assert config.app_name == "test-app"
        assert config.environment == "production"
        assert config.version == "2.0.0"
        assert config.default_level == LogLevel.WARNING
        assert config.correlation_id_header == "X-Request-ID"
        assert config.enable_correlation_ids is False
        assert config.enable_structured_context is False
        assert config.max_context_size == 5000
        assert config.async_queue_size == 5000
        assert config.enable_performance_metrics is True
        assert config.enable_sanitization is False
        assert config.sensitive_fields == sensitive_fields
        assert config.backends == backends
        assert config.enable_singleton is True
        assert config.singleton_name == "custom"

    def test_global_logger_config_context_size_validation(self) -> None:
        """Test max_context_size validation."""
        with pytest.raises(ValidationError):
            GlobalLoggerConfig(max_context_size=0)

    def test_global_logger_config_queue_size_validation(self) -> None:
        """Test async_queue_size validation."""
        with pytest.raises(ValidationError):
            GlobalLoggerConfig(async_queue_size=0)

    def test_global_logger_config_default_backends_validation(self) -> None:
        """Test that default console backend is added when no backends provided."""
        config = GlobalLoggerConfig(backends=[])
        assert len(config.backends) == 1
        assert isinstance(config.backends[0], ConsoleBackendConfig)
        assert config.backends[0].name == "default_console"

    def test_global_logger_config_duplicate_backend_names(self) -> None:
        """Test validation of duplicate backend names."""
        backends: list[
            ConsoleBackendConfig
            | FileBackendConfig
            | RestApiBackendConfig
            | WebSocketBackendConfig
            | DatabaseBackendConfig
        ] = [
            ConsoleBackendConfig(name="duplicate"),
            FileBackendConfig(name="duplicate"),
        ]
        with pytest.raises(JPYLoggerConfigurationError) as exc_info:
            GlobalLoggerConfig(backends=backends)

        assert "Backend names must be unique" in str(exc_info.value)
        assert exc_info.value.error_details.details is not None

        assert exc_info.value.error_details.details["config_section"] == "backends"

    def test_global_logger_config_from_env_basic(self) -> None:
        """Test creating config from environment variables."""
        env_vars = {
            "LOGGER_APP_NAME": "env-app",
            "LOGGER_ENVIRONMENT": "staging",
            "LOGGER_VERSION": "3.0.0",
            "LOGGER_LEVEL": "debug",
            "LOGGER_CORRELATION_HEADER": "X-Trace-ID",
            "LOGGER_ENABLE_CORRELATION": "true",
            "LOGGER_ENABLE_STRUCTURED": "false",
            "LOGGER_MAX_CONTEXT_SIZE": "20000",
            "LOGGER_QUEUE_SIZE": "15000",
            "LOGGER_ENABLE_METRICS": "yes",
            "LOGGER_ENABLE_SANITIZATION": "no",
            "LOGGER_ENABLE_SINGLETON": "1",
            "LOGGER_SINGLETON_NAME": "env-singleton",
        }

        with patch.dict(os.environ, env_vars):
            config = GlobalLoggerConfig.from_env()

        assert config.app_name == "env-app"
        assert config.environment == "staging"
        assert config.version == "3.0.0"
        assert config.default_level == LogLevel.DEBUG
        assert config.correlation_id_header == "X-Trace-ID"
        assert config.enable_correlation_ids is True
        assert config.enable_structured_context is False
        assert config.max_context_size == 20000
        assert config.async_queue_size == 15000
        assert config.enable_performance_metrics is True
        assert config.enable_sanitization is False
        assert config.enable_singleton is True
        assert config.singleton_name == "env-singleton"

    def test_global_logger_config_from_env_boolean_variations(self) -> None:
        """Test different boolean value formats from environment."""
        test_cases = [
            ("true", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("0", False),
            ("no", False),
            ("off", False),
            ("invalid", False),
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {"LOGGER_ENABLE_CORRELATION": env_value}):
                config = GlobalLoggerConfig.from_env()
                assert config.enable_correlation_ids == expected

    def test_global_logger_config_from_env_sensitive_fields(self) -> None:
        """Test sensitive fields from environment variable."""
        with patch.dict(
            os.environ, {"LOGGER_SENSITIVE_FIELDS": "password,token,secret,api_key"}
        ):
            config = GlobalLoggerConfig.from_env()
            assert config.sensitive_fields == ["password", "token", "secret", "api_key"]

    def test_global_logger_config_from_env_custom_prefix(self) -> None:
        """Test custom environment variable prefix."""
        env_vars = {
            "CUSTOM_APP_NAME": "custom-app",
            "CUSTOM_ENVIRONMENT": "test",
        }

        with patch.dict(os.environ, env_vars):
            config = GlobalLoggerConfig.from_env(prefix="CUSTOM_")

        assert config.app_name == "custom-app"
        assert config.environment == "test"

    def test_global_logger_config_from_env_missing_vars(self) -> None:
        """Test behavior when environment variables are missing."""
        # Clear environment to ensure no relevant vars exist
        with patch.dict(os.environ, {}, clear=True):
            config = GlobalLoggerConfig.from_env()

        # Should use defaults when env vars are missing
        assert config.app_name == "jinpy-utils"
        assert config.environment == "development"

    def test_global_logger_config_from_env_integer_conversion_error(self) -> None:
        """Test integer conversion error handling."""
        with patch.dict(os.environ, {"LOGGER_MAX_CONTEXT_SIZE": "invalid"}):
            with pytest.raises(ValueError):
                GlobalLoggerConfig.from_env()


class TestLoggerConfig:
    """Test LoggerConfig functionality."""

    def test_logger_config_basic(self) -> None:
        """Test basic LoggerConfig creation."""
        config = LoggerConfig(name="test-logger")
        assert config.name == "test-logger"
        assert config.level is None
        assert config.backends is None
        assert config.context == {}
        assert config.correlation_id is None

    def test_logger_config_with_values(self) -> None:
        """Test LoggerConfig with custom values."""
        context = {"service": "api", "version": "1.0"}
        backends = ["console", "file"]

        config = LoggerConfig(
            name="api-logger",
            level=LogLevel.DEBUG,
            backends=backends,
            context=context,
            correlation_id="test-correlation-123",
        )
        assert config.name == "api-logger"
        assert config.level == LogLevel.DEBUG
        assert config.backends == backends
        assert config.context == context
        assert config.correlation_id == "test-correlation-123"

    def test_logger_config_extra_fields_allowed(self) -> None:
        """Test that extra fields are allowed."""
        config = LoggerConfig(
            name="test",
            custom_field="custom_value",  # type:ignore
        )
        assert getattr(config, "custom_field", None) == "custom_value"

    def test_logger_config_json_serialization(self) -> None:
        """Test JSON serialization of LoggerConfig."""
        config = LoggerConfig(
            name="test-logger",
            level=LogLevel.INFO,
            backends=["console"],
            context={"key": "value"},
        )
        json_str = config.model_dump_json()
        data = json.loads(json_str)
        assert data["name"] == "test-logger"
        assert data["level"] == "info"
        assert data["backends"] == ["console"]
        assert data["context"]["key"] == "value"


class TestFactoryFunctions:
    """Test configuration factory functions."""

    def test_create_development_config(self) -> None:
        """Test development configuration factory."""
        config = create_development_config()
        assert config.environment == "development"
        assert config.default_level == LogLevel.DEBUG
        assert len(config.backends) == 1
        assert isinstance(config.backends[0], ConsoleBackendConfig)
        assert config.backends[0].name == "dev_console"
        assert config.backends[0].colors is True
        assert config.backends[0].format == LogFormat.CONSOLE

    def test_create_production_config(self) -> None:
        """Test production configuration factory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("jinpy_utils.logger.config.Path") as mock_path:
                mock_path.return_value = Path(temp_dir) / "app.log"
                config = create_production_config()

        assert config.environment == "production"
        assert config.default_level == LogLevel.INFO
        assert config.enable_performance_metrics is True
        assert len(config.backends) == 1
        assert isinstance(config.backends[0], FileBackendConfig)
        assert config.backends[0].name == "prod_file"
        assert config.backends[0].format == LogFormat.JSON
        assert config.backends[0].max_size_mb == 100
        assert config.backends[0].backup_count == 10

    def test_create_cloud_config(self) -> None:
        """Test cloud configuration factory."""
        api_url = "https://logs.example.com"
        api_key = "test-api-key"

        config = create_cloud_config(api_url, api_key)
        assert config.environment == "cloud"
        assert config.default_level == LogLevel.INFO
        assert len(config.backends) == 1
        assert isinstance(config.backends[0], RestApiBackendConfig)
        assert config.backends[0].name == "cloud_api"
        assert config.backends[0].base_url == api_url
        assert config.backends[0].security.level == SecurityLevel.API_KEY
        assert config.backends[0].security.api_key == api_key
        assert config.backends[0].batch_strategy == BatchStrategy.HYBRID


class TestConfigIntegration:
    """Test integration scenarios and complex configurations."""

    def test_complex_configuration_serialization(self) -> None:
        """Test serialization of complex configuration."""
        security = SecurityConfig(
            level=SecurityLevel.TLS,
            api_key="test-key",
            verify_ssl=False,
        )
        retry = RetryConfig(
            strategy=RetryStrategy.LINEAR,
            max_attempts=5,
        )
        backend = RestApiBackendConfig(
            name="complex-api",
            base_url="https://api.example.com",
            security=security,
            retry=retry,
        )
        config = GlobalLoggerConfig(
            app_name="complex-app",
            backends=[backend],
        )

        # Test JSON serialization
        json_str = config.model_dump_json()
        data = json.loads(json_str)

        assert data["app_name"] == "complex-app"
        assert data["backends"][0]["name"] == "complex-api"
        assert data["backends"][0]["security"]["level"] == "tls"
        assert data["backends"][0]["retry"]["strategy"] == "linear"

    def test_configuration_deserialization(self) -> None:
        """Test creating configuration from dictionary."""
        config_dict = {
            "app_name": "deserialized-app",
            "environment": "test",
            "default_level": "warning",
            "backends": [
                {
                    "backend_type": "console",
                    "name": "test-console",
                    "colors": False,
                }
            ],
        }

        config = GlobalLoggerConfig.model_validate(config_dict)
        assert config.app_name == "deserialized-app"
        assert config.environment == "test"
        assert config.default_level == LogLevel.WARNING
        assert len(config.backends) == 1
        assert isinstance(config.backends[0], ConsoleBackendConfig)
        assert config.backends[0].colors is False

    def test_nested_configuration_validation(self) -> None:
        """Test validation of nested configuration objects."""
        # Test that invalid nested config raises validation error
        with pytest.raises(ValidationError):
            GlobalLoggerConfig(
                backends=[
                    FileBackendConfig(
                        name="invalid-file",
                        max_size_mb=-1,
                    )
                ]
            )

    def test_configuration_inheritance_and_overrides(self) -> None:
        """Test configuration inheritance and field overrides."""
        base_config = GlobalLoggerConfig(
            app_name="base-app",
            default_level=LogLevel.INFO,
        )

        # Create new config with some overrides
        override_dict = base_config.model_dump()
        override_dict["app_name"] = "overridden-app"
        override_dict["default_level"] = "debug"

        new_config = GlobalLoggerConfig(**override_dict)
        assert new_config.app_name == "overridden-app"
        assert new_config.default_level == LogLevel.DEBUG
        # Other fields should remain the same
        assert new_config.environment == base_config.environment

    def test_all_backend_types_in_single_config(self) -> None:
        """Test configuration with all backend types."""
        backends: list[
            ConsoleBackendConfig
            | FileBackendConfig
            | RestApiBackendConfig
            | WebSocketBackendConfig
            | DatabaseBackendConfig
        ] = [
            ConsoleBackendConfig(name="console"),
            FileBackendConfig(name="file"),
            RestApiBackendConfig(name="api", base_url="https://api.example.com"),
            WebSocketBackendConfig(name="ws", ws_url="wss://api.example.com/ws"),
            DatabaseBackendConfig(name="db", connection_string="sqlite:///test.db"),
        ]

        config = GlobalLoggerConfig(backends=backends)
        assert len(config.backends) == 5

        # Verify each backend type
        backend_types = [backend.backend_type for backend in config.backends]
        expected_types = [
            BackendType.CONSOLE,
            BackendType.FILE,
            BackendType.REST_API,
            BackendType.WEBSOCKET,
            BackendType.DATABASE,
        ]
        assert set(backend_types) == set(expected_types)

    def test_environment_variable_integration(self) -> None:
        """Test full environment variable integration."""
        env_vars = {
            "LOGGER_APP_NAME": "env-integration-test",
            "LOGGER_ENABLE_METRICS": "true",
            "LOGGER_SENSITIVE_FIELDS": "password,secret,token",
            "TEST_API_KEY": "env-resolved-key",
        }

        with patch.dict(os.environ, env_vars):
            # Create config from environment
            config = GlobalLoggerConfig.from_env()

            # Add backend with environment variable reference
            backend = RestApiBackendConfig(
                name="env-backend",
                base_url="https://api.example.com",
                security=SecurityConfig(api_key="${TEST_API_KEY}"),
            )
            config.backends.append(backend)

        assert config.app_name == "env-integration-test"
        assert config.enable_performance_metrics is True
        assert config.sensitive_fields == ["password", "secret", "token"]
        assert config.backends[-1].security.api_key == "env-resolved-key"

    def test_configuration_edge_cases(self) -> None:
        """Test edge cases and boundary conditions."""
        # Test with minimal valid configuration
        minimal_config = GlobalLoggerConfig(
            max_context_size=1,
            async_queue_size=1,
        )
        assert minimal_config.max_context_size == 1
        assert minimal_config.async_queue_size == 1

        # Test with maximum valid retry attempts
        retry_config = RetryConfig(max_attempts=10)
        assert retry_config.max_attempts == 10

        # Test with minimum valid retry attempts
        retry_config_min = RetryConfig(max_attempts=1)
        assert retry_config_min.max_attempts == 1

    def test_configuration_model_validation_edge_cases(self) -> None:
        """Test model validation edge cases."""
        # Test empty backends list gets default console backend
        config = GlobalLoggerConfig(backends=[])
        assert len(config.backends) == 1
        assert config.backends[0].name == "default_console"

        # Test that providing backends prevents default creation
        custom_backend = FileBackendConfig(name="custom")
        config_with_backends = GlobalLoggerConfig(backends=[custom_backend])
        assert len(config_with_backends.backends) == 1
        assert config_with_backends.backends[0].name == "custom"
