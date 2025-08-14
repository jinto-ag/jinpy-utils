"""Tests for logger exception classes."""

import json

from jinpy_utils.base.exceptions import JPYLoggingError
from jinpy_utils.logger.exceptions import (
    JPYLoggerBackendError,
    JPYLoggerConfigurationError,
    JPYLoggerConnectionError,
    JPYLoggerError,
    JPYLoggerPerformanceError,
    JPYLoggerSecurityError,
    JPYLoggerWebSocketError,
)


class TestJPYLoggerError:
    """Test JPYLoggerError specific functionality."""

    def test_logger_error_basic(self) -> None:
        """Test basic JPYLoggerError creation."""
        exc = JPYLoggerError(message="Logger operation failed")
        assert exc.error_details.error_code == "LOGGING_ERROR"
        assert exc.error_details.message == "Logger operation failed"
        assert exc.error_details.suggestions is not None
        assert len(exc.error_details.suggestions) > 0
        assert "Check logger configuration" in exc.error_details.suggestions
        assert "Verify logging permissions" in exc.error_details.suggestions
        assert "Ensure proper initialization" in exc.error_details.suggestions

    def test_logger_error_with_details(self) -> None:
        """Test JPYLoggerError with detailed parameters."""
        exc = JPYLoggerError(
            message="Logger operation failed",
            logger_name="app.database",
            operation="log_write",
            handler_type="CustomHandler",
        )
        assert exc.error_details.error_code == "LOGGING_ERROR"
        assert exc.error_details.details is not None
        assert exc.error_details.details["logger_name"] == "app.database"
        assert exc.error_details.details["operation"] == "log_write"
        assert exc.error_details.details["handler_type"] == "CustomHandler"

    def test_logger_error_with_none_parameters(self) -> None:
        """Test JPYLoggerError with None parameters."""
        exc = JPYLoggerError(
            message="Logger error with none params",
            logger_name=None,
            operation=None,
        )
        assert exc.error_details.error_code == "LOGGING_ERROR"
        assert exc.error_details.details is not None
        assert "logger_name" not in exc.error_details.details
        assert "operation" not in exc.error_details.details

    def test_logger_error_custom_suggestions_override(self) -> None:
        """Test that custom suggestions override defaults."""
        custom_suggestions = [
            "Custom logger suggestion 1",
            "Custom logger suggestion 2",
        ]
        exc = JPYLoggerError(
            message="Logger error",
            suggestions=custom_suggestions,
        )
        assert exc.error_details.suggestions == custom_suggestions

    def test_logger_error_additional_details(self) -> None:
        """Test JPYLoggerError with additional details in kwargs."""
        exc = JPYLoggerError(
            message="Logger error with extra details",
            logger_name="test.logger",
            details={"existing": "detail"},
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["logger_name"] == "test.logger"
        assert exc.error_details.details["existing"] == "detail"

    def test_logger_error_inheritance(self) -> None:
        """Test that JPYLoggerError inherits from JPYLoggingError."""
        exc = JPYLoggerError(message="Inheritance test")
        assert isinstance(exc, JPYLoggingError)
        assert isinstance(exc, Exception)


class TestJPYLoggerConfigurationError:
    """Test JPYLoggerConfigurationError specific functionality."""

    def test_configuration_error_basic(self) -> None:
        """Test basic JPYLoggerConfigurationError creation."""
        exc = JPYLoggerConfigurationError(
            message="Invalid logger configuration",
        )
        assert exc.error_details.error_code == "LOGGING_ERROR"
        assert exc.error_details.message == "Invalid logger configuration"
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerConfiguration"
        assert exc.error_details.suggestions is not None
        assert "Check logger configuration syntax" in exc.error_details.suggestions
        assert "Verify all required settings" in exc.error_details.suggestions
        assert "Ensure valid configuration values" in exc.error_details.suggestions

    def test_configuration_error_with_details(self) -> None:
        """Test JPYLoggerConfigurationError with detailed parameters."""
        exc = JPYLoggerConfigurationError(
            message="Invalid configuration",
            config_section="handlers",
            config_value={"invalid": "config"},
            logger_name="app.logger",
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["config_section"] == "handlers"
        assert exc.error_details.details["config_value"] == str(
            {"invalid": "config"},
        )
        assert exc.error_details.details["logger_name"] == "app.logger"
        assert exc.error_details.details["handler_type"] == "LoggerConfiguration"

    def test_configuration_error_with_none_parameters(self) -> None:
        """Test JPYLoggerConfigurationError with None parameters."""
        exc = JPYLoggerConfigurationError(
            message="Config error with none params",
            config_section=None,
            config_value=None,
            logger_name=None,
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerConfiguration"
        assert "config_section" not in exc.error_details.details
        assert "config_value" not in exc.error_details.details
        assert "logger_name" not in exc.error_details.details

    def test_configuration_error_with_zero_value(self) -> None:
        """Test JPYLoggerConfigurationError with config_value=0."""
        exc = JPYLoggerConfigurationError(
            message="Config error with zero value",
            config_section="logging",
            config_value=0,
            logger_name="test.logger",
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["config_value"] == "0"
        assert exc.error_details.details["config_section"] == "logging"

    def test_configuration_error_custom_suggestions_override(self) -> None:
        """Test that custom suggestions override defaults."""
        custom_suggestions = ["Custom config suggestion"]
        exc = JPYLoggerConfigurationError(
            message="Config error",
            suggestions=custom_suggestions,
        )
        assert exc.error_details.suggestions == custom_suggestions

    def test_configuration_error_inheritance(self) -> None:
        """
        Test that JPYLoggerConfigurationError inherits from JPYLoggingError.
        """
        exc = JPYLoggerConfigurationError(message="Inheritance test")
        assert isinstance(exc, JPYLoggingError)


class TestJPYLoggerBackendError:
    """Test JPYLoggerBackendError specific functionality."""

    def test_backend_error_basic(self) -> None:
        """Test basic JPYLoggerBackendError creation."""
        exc = JPYLoggerBackendError(message="Backend operation failed")
        assert exc.error_details.error_code == "LOGGING_ERROR"
        assert exc.error_details.message == "Backend operation failed"
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerBackend"
        assert exc.error_details.suggestions is not None
        assert "Check backend connectivity" in exc.error_details.suggestions
        assert "Verify backend configuration" in exc.error_details.suggestions
        assert (
            "Ensure backend dependencies are installed" in exc.error_details.suggestions
        )

    def test_backend_error_with_details(self) -> None:
        """Test JPYLoggerBackendError with detailed parameters."""
        backend_config = {"host": "localhost", "port": 5432}
        exc = JPYLoggerBackendError(
            message="Backend connection failed",
            backend_type="elasticsearch",
            backend_config=backend_config,
            logger_name="search.logger",
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["backend_type"] == "elasticsearch"
        assert exc.error_details.details["backend_config"] == backend_config
        assert exc.error_details.details["logger_name"] == "search.logger"
        assert (
            exc.error_details.details["handler_type"] == "LoggerBackend:elasticsearch"
        )

    def test_backend_error_with_none_parameters(self) -> None:
        """Test JPYLoggerBackendError with None parameters."""
        exc = JPYLoggerBackendError(
            message="Backend error with none params",
            backend_type=None,
            backend_config=None,
            logger_name=None,
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerBackend"
        assert "backend_type" not in exc.error_details.details
        assert "backend_config" not in exc.error_details.details
        assert "logger_name" not in exc.error_details.details

    def test_backend_error_handler_type_with_backend_type(self) -> None:
        """Test handler_type formatting with backend_type."""
        exc = JPYLoggerBackendError(
            message="Backend error",
            backend_type="redis",
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerBackend:redis"

    def test_backend_error_custom_suggestions_override(self) -> None:
        """Test that custom suggestions override defaults."""
        custom_suggestions = ["Custom backend suggestion"]
        exc = JPYLoggerBackendError(
            message="Backend error",
            suggestions=custom_suggestions,
        )
        assert exc.error_details.suggestions == custom_suggestions

    def test_backend_error_inheritance(self) -> None:
        """Test that JPYLoggerBackendError inherits from JPYLoggingError."""
        exc = JPYLoggerBackendError(message="Inheritance test")
        assert isinstance(exc, JPYLoggingError)


class TestJPYLoggerConnectionError:
    """Test JPYLoggerConnectionError specific functionality."""

    def test_connection_error_basic(self) -> None:
        """Test basic JPYLoggerConnectionError creation."""
        exc = JPYLoggerConnectionError(message="Logger connection failed")
        assert exc.error_details.error_code == "LOGGING_ERROR"
        assert exc.error_details.message == "Logger connection failed"
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerConnection"
        assert exc.error_details.suggestions is not None
        assert "Check network connectivity" in exc.error_details.suggestions
        assert "Verify endpoint availability" in exc.error_details.suggestions
        assert "Check firewall settings" in exc.error_details.suggestions
        assert "Validate authentication credentials" in exc.error_details.suggestions

    def test_connection_error_with_details(self) -> None:
        """Test JPYLoggerConnectionError with detailed parameters."""
        exc = JPYLoggerConnectionError(
            message="Connection failed",
            endpoint="https://logs.example.com",
            connection_type="HTTPS",
            logger_name="remote.logger",
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["endpoint"] == "https://logs.example.com"
        assert exc.error_details.details["connection_type"] == "HTTPS"
        assert exc.error_details.details["logger_name"] == "remote.logger"
        assert exc.error_details.details["handler_type"] == "LoggerConnection:HTTPS"

    def test_connection_error_with_none_parameters(self) -> None:
        """Test JPYLoggerConnectionError with None parameters."""
        exc = JPYLoggerConnectionError(
            message="Connection error with none params",
            endpoint=None,
            connection_type=None,
            logger_name=None,
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerConnection"
        assert "endpoint" not in exc.error_details.details
        assert "connection_type" not in exc.error_details.details
        assert "logger_name" not in exc.error_details.details

    def test_connection_error_handler_type_with_connection_type(self) -> None:
        """Test handler_type formatting with connection_type."""
        exc = JPYLoggerConnectionError(
            message="Connection error",
            connection_type="TCP",
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerConnection:TCP"

    def test_connection_error_custom_suggestions_override(self) -> None:
        """Test that custom suggestions override defaults."""
        custom_suggestions = ["Custom connection suggestion"]
        exc = JPYLoggerConnectionError(
            message="Connection error",
            suggestions=custom_suggestions,
        )
        assert exc.error_details.suggestions == custom_suggestions

    def test_connection_error_inheritance(self) -> None:
        """Test that JPYLoggerConnectionError inherits from JPYLoggingError."""
        exc = JPYLoggerConnectionError(message="Inheritance test")
        assert isinstance(exc, JPYLoggingError)


class TestJPYLoggerSecurityError:
    """Test JPYLoggerSecurityError specific functionality."""

    def test_security_error_basic(self) -> None:
        """Test basic JPYLoggerSecurityError creation."""
        exc = JPYLoggerSecurityError(message="Logger security violation")
        assert exc.error_details.error_code == "LOGGING_ERROR"
        assert exc.error_details.message == "Logger security violation"
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerSecurity"
        assert exc.error_details.suggestions is not None
        assert "Check authentication credentials" in exc.error_details.suggestions
        assert "Verify API key permissions" in exc.error_details.suggestions
        assert "Ensure secure connection" in exc.error_details.suggestions
        assert "Review security policies" in exc.error_details.suggestions

    def test_security_error_with_details(self) -> None:
        """Test JPYLoggerSecurityError with detailed parameters."""
        exc = JPYLoggerSecurityError(
            message="Authentication failed",
            security_context="API_KEY_INVALID",
            logger_name="secure.logger",
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["security_context"] == "API_KEY_INVALID"
        assert exc.error_details.details["logger_name"] == "secure.logger"
        assert exc.error_details.details["handler_type"] == "LoggerSecurity"

    def test_security_error_with_none_parameters(self) -> None:
        """Test JPYLoggerSecurityError with None parameters."""
        exc = JPYLoggerSecurityError(
            message="Security error with none params",
            security_context=None,
            logger_name=None,
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerSecurity"
        assert "security_context" not in exc.error_details.details
        assert "logger_name" not in exc.error_details.details

    def test_security_error_custom_suggestions_override(self) -> None:
        """Test that custom suggestions override defaults."""
        custom_suggestions = ["Custom security suggestion"]
        exc = JPYLoggerSecurityError(
            message="Security error",
            suggestions=custom_suggestions,
        )
        assert exc.error_details.suggestions == custom_suggestions

    def test_security_error_inheritance(self) -> None:
        """Test that JPYLoggerSecurityError inherits from JPYLoggingError."""
        exc = JPYLoggerSecurityError(message="Inheritance test")
        assert isinstance(exc, JPYLoggingError)


class TestJPYLoggerPerformanceError:
    """Test JPYLoggerPerformanceError specific functionality."""

    def test_performance_error_basic(self) -> None:
        """Test basic JPYLoggerPerformanceError creation."""
        exc = JPYLoggerPerformanceError(message="Logger performance issue")
        assert exc.error_details.error_code == "LOGGING_ERROR"
        assert exc.error_details.message == "Logger performance issue"
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerPerformance"
        assert exc.error_details.suggestions is not None
        assert "Increase buffer sizes" in exc.error_details.suggestions
        assert "Reduce log frequency" in exc.error_details.suggestions
        assert "Optimize backend configuration" in exc.error_details.suggestions
        assert "Scale backend resources" in exc.error_details.suggestions

    def test_performance_error_with_details(self) -> None:
        """Test JPYLoggerPerformanceError with detailed parameters."""
        exc = JPYLoggerPerformanceError(
            message="Performance threshold exceeded",
            performance_metric="latency",
            threshold_value=100.0,
            actual_value=250.5,
            logger_name="perf.logger",
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["performance_metric"] == "latency"
        assert exc.error_details.details["threshold_value"] == 100.0
        assert exc.error_details.details["actual_value"] == 250.5
        assert exc.error_details.details["logger_name"] == "perf.logger"
        assert exc.error_details.details["handler_type"] == "LoggerPerformance"

    def test_performance_error_with_none_parameters(self) -> None:
        """Test JPYLoggerPerformanceError with None parameters."""
        exc = JPYLoggerPerformanceError(
            message="Performance error with none params",
            performance_metric=None,
            threshold_value=None,
            actual_value=None,
            logger_name=None,
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerPerformance"
        assert "performance_metric" not in exc.error_details.details
        assert "threshold_value" not in exc.error_details.details
        assert "actual_value" not in exc.error_details.details
        assert "logger_name" not in exc.error_details.details

    def test_performance_error_with_zero_values(self) -> None:
        """Test JPYLoggerPerformanceError with zero values."""
        exc = JPYLoggerPerformanceError(
            message="Performance error with zero values",
            performance_metric="throughput",
            threshold_value=0.0,
            actual_value=0.0,
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["threshold_value"] == 0.0
        assert exc.error_details.details["actual_value"] == 0.0

    def test_performance_error_custom_suggestions_override(self) -> None:
        """Test that custom suggestions override defaults."""
        custom_suggestions = ["Custom performance suggestion"]
        exc = JPYLoggerPerformanceError(
            message="Performance error",
            suggestions=custom_suggestions,
        )
        assert exc.error_details.suggestions == custom_suggestions

    def test_performance_error_inheritance(self) -> None:
        """Test that JPYLoggerPerformanceError inherits from JPYLoggingError."""
        exc = JPYLoggerPerformanceError(message="Inheritance test")
        assert isinstance(exc, JPYLoggingError)


class TestJPYLoggerWebSocketError:
    """Test JPYLoggerWebSocketError specific functionality."""

    def test_websocket_error_basic(self) -> None:
        """Test basic JPYLoggerWebSocketError creation."""
        exc = JPYLoggerWebSocketError(message="WebSocket logger error")
        assert exc.error_details.error_code == "LOGGING_ERROR"
        assert exc.error_details.message == "WebSocket logger error"
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerWebSocket"
        assert exc.error_details.suggestions is not None
        assert "Check WebSocket endpoint availability" in exc.error_details.suggestions
        assert "Verify WebSocket connection state" in exc.error_details.suggestions
        assert "Check network connectivity" in exc.error_details.suggestions
        assert "Review WebSocket authentication" in exc.error_details.suggestions

    def test_websocket_error_with_details(self) -> None:
        """Test JPYLoggerWebSocketError with detailed parameters."""
        exc = JPYLoggerWebSocketError(
            message="WebSocket connection failed",
            ws_endpoint="wss://logs.example.com/ws",
            ws_state="CONNECTING",
            logger_name="ws.logger",
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["ws_endpoint"] == "wss://logs.example.com/ws"
        assert exc.error_details.details["ws_state"] == "CONNECTING"
        assert exc.error_details.details["logger_name"] == "ws.logger"
        assert exc.error_details.details["handler_type"] == "LoggerWebSocket"

    def test_websocket_error_with_none_parameters(self) -> None:
        """Test JPYLoggerWebSocketError with None parameters."""
        exc = JPYLoggerWebSocketError(
            message="WebSocket error with none params",
            ws_endpoint=None,
            ws_state=None,
            logger_name=None,
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "LoggerWebSocket"
        assert "ws_endpoint" not in exc.error_details.details
        assert "ws_state" not in exc.error_details.details
        assert "logger_name" not in exc.error_details.details

    def test_websocket_error_custom_suggestions_override(self) -> None:
        """Test that custom suggestions override defaults."""
        custom_suggestions = ["Custom WebSocket suggestion"]
        exc = JPYLoggerWebSocketError(
            message="WebSocket error",
            suggestions=custom_suggestions,
        )
        assert exc.error_details.suggestions == custom_suggestions

    def test_websocket_error_inheritance(self) -> None:
        """Test that JPYLoggerWebSocketError inherits from JPYLoggingError."""
        exc = JPYLoggerWebSocketError(message="Inheritance test")
        assert isinstance(exc, JPYLoggingError)


class TestLoggerExceptionsIntegration:
    """Test integration scenarios and edge cases for logger exceptions."""

    def test_all_logger_exceptions_inheritance(self) -> None:
        """Test that all logger exceptions inherit from JPYLoggingError."""
        exceptions = [
            JPYLoggerError("test"),
            JPYLoggerConfigurationError("test"),
            JPYLoggerBackendError("test"),
            JPYLoggerConnectionError("test"),
            JPYLoggerSecurityError("test"),
            JPYLoggerPerformanceError("test"),
            JPYLoggerWebSocketError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, JPYLoggingError)
            assert isinstance(exc, Exception)

    def test_exception_serialization_all_types(self) -> None:
        """Test JSON serialization for all logger exception types."""
        exceptions = [
            JPYLoggerError("test", logger_name="test.logger"),
            JPYLoggerConfigurationError("test", config_section="handlers"),
            JPYLoggerBackendError("test", backend_type="redis"),
            JPYLoggerConnectionError("test", endpoint="http://example.com"),
            JPYLoggerSecurityError("test", security_context="AUTH_FAILED"),
            JPYLoggerPerformanceError("test", performance_metric="latency"),
            JPYLoggerWebSocketError("test", ws_endpoint="ws://example.com"),
        ]

        for exc in exceptions:
            json_str = exc.to_json()
            data = json.loads(json_str)
            assert data["error_code"] == "LOGGING_ERROR"
            assert "timestamp" in data
            assert "details" in data

    def test_exception_details_merging(self) -> None:
        """Test that details are properly merged with existing details."""
        existing_details = {"existing_key": "existing_value"}
        exc = JPYLoggerError(
            message="Test details merging",
            logger_name="test.logger",
            details=existing_details,
        )

        # Both existing and new details should be present
        assert exc.error_details.details is not None
        assert exc.error_details.details["existing_key"] == "existing_value"
        assert exc.error_details.details["logger_name"] == "test.logger"

    def test_complex_backend_config_serialization(self) -> None:
        """Test serialization with complex backend configuration."""
        complex_config = {
            "hosts": ["host1", "host2"],
            "settings": {"timeout": 30, "retries": 3},
            "nested": {"deep": {"value": 42}},
        }

        exc = JPYLoggerBackendError(
            message="Complex config test",
            backend_config=complex_config,
        )

        json_str = exc.to_json()
        data = json.loads(json_str)
        assert data["details"]["backend_config"] == complex_config

    def test_exception_with_empty_collections(self) -> None:
        """Test exceptions with empty collections in details."""
        exc = JPYLoggerError(
            message="Empty collections test",
            details={},
            suggestions=[],
        )

        assert exc.error_details.details == {
            "handler_type": "Logger",
        }
        assert exc.error_details.suggestions == []

    def test_performance_error_edge_cases(self) -> None:
        """Test JPYLoggerPerformanceError with edge case values."""
        # Test with negative values
        exc = JPYLoggerPerformanceError(
            message="Negative values test",
            threshold_value=-1.0,
            actual_value=-5.0,
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["threshold_value"] == -1.0
        assert exc.error_details.details["actual_value"] == -5.0

        # Test with very large values
        exc = JPYLoggerPerformanceError(
            message="Large values test",
            threshold_value=1e10,
            actual_value=1e15,
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["threshold_value"] == 1e10
        assert exc.error_details.details["actual_value"] == 1e15

    def test_all_handler_types_formatting(self) -> None:
        """Test handler_type formatting for all exception types."""
        # Test base handler type
        exc: JPYLoggingError = JPYLoggerError("test")
        assert exc.error_details.details is not None
        assert exc.error_details.details["handler_type"] == "Logger"

        # Test configuration handler type
        details = JPYLoggerConfigurationError("test").error_details.details
        assert details is not None
        assert details["handler_type"] == "LoggerConfiguration"

        # Test backend handler type without backend_type
        details = JPYLoggerBackendError("test").error_details.details
        assert details is not None
        assert details["handler_type"] == "LoggerBackend"

        # Test backend handler type with backend_type
        details = JPYLoggerBackendError(
            "test", backend_type="mysql"
        ).error_details.details
        assert details is not None
        assert details["handler_type"] == "LoggerBackend:mysql"

        # Test connection handler type without connection_type
        details = JPYLoggerConnectionError("test").error_details.details
        assert details is not None
        assert details["handler_type"] == "LoggerConnection"

        # Test connection handler type with connection_type
        details = JPYLoggerConnectionError(
            "test", connection_type="HTTP"
        ).error_details.details
        assert details is not None
        assert details["handler_type"] == "LoggerConnection:HTTP"

        # Test security handler type
        details = JPYLoggerSecurityError("test").error_details.details
        assert details is not None
        assert details["handler_type"] == "LoggerSecurity"

        # Test performance handler type
        details = JPYLoggerPerformanceError("test").error_details.details
        assert details is not None
        assert details["handler_type"] == "LoggerPerformance"

        # Test websocket handler type
        details = JPYLoggerWebSocketError("test").error_details.details
        assert details is not None
        assert details["handler_type"] == "LoggerWebSocket"
