"""Tests for base exception classes."""

import json
from datetime import datetime
from typing import Any

from jinpy_utils.base import (
    ErrorDetails,
    ExceptionRegistry,
    JPYBaseException,
    JPYCacheError,
    JPYConfigurationError,
    JPYDatabaseError,
    JPYValidationError,
    create_exception,
)
from jinpy_utils.base.exceptions import (
    JPYConnectionError,
    JPYLoggingError,
    register_exception,
)


class TestErrorDetails:
    """Test ErrorDetails Pydantic model."""

    def test_error_details_creation(self) -> None:
        """Test basic ErrorDetails creation."""
        details = ErrorDetails(
            error_code="TEST_001",
            message="Test error message",
        )

        assert details.error_code == "TEST_001"
        assert details.message == "Test error message"
        assert isinstance(details.timestamp, datetime)
        assert details.details is None
        assert details.context is None
        assert details.suggestions is None

    def test_error_details_with_optional_fields(self) -> None:
        """Test ErrorDetails with all optional fields."""
        details = ErrorDetails(
            error_code="TEST_002",
            message="Test error with details",
            details={"key": "value"},
            context={"function": "test_function"},
            suggestions=["Try this", "Or this"],
        )

        assert details.details == {"key": "value"}
        assert details.context == {"function": "test_function"}
        assert details.suggestions == ["Try this", "Or this"]

    def test_error_details_json_serialization(self) -> None:
        """Test JSON serialization of ErrorDetails."""
        details = ErrorDetails(
            error_code="TEST_003",
            message="Serialization test",
        )

        json_str = details.model_dump_json()
        assert isinstance(json_str, str)

        # Parse back to verify
        data = json.loads(json_str)
        assert data["error_code"] == "TEST_003"
        assert data["message"] == "Serialization test"
        assert "timestamp" in data

    def test_error_details_datetime_encoding(self) -> None:
        """Test datetime JSON encoding in ErrorDetails."""
        details = ErrorDetails(error_code="TEST_004", message="Datetime test")

        data = details.model_dump()
        assert isinstance(data["timestamp"], datetime)

        json_str = details.model_dump_json()
        data = json.loads(json_str)
        assert isinstance(data["timestamp"], str)


class TestJPYBaseException:
    """Test base exception class."""

    def test_base_exception_creation(self) -> None:
        """Test basic exception creation."""
        exc = JPYBaseException(
            error_code="BASE_001",
            message="Base exception test",
        )

        assert str(exc) == "[BASE_001] Base exception test"
        assert exc.error_details.error_code == "BASE_001"
        assert exc.error_details.message == "Base exception test"

    def test_base_exception_with_details(self) -> None:
        """Test exception with additional details."""
        exc = JPYBaseException(
            error_code="BASE_002",
            message="Exception with details",
            details={"param": "value"},
            context={"module": "test"},
            suggestions=["Check configuration"],
        )

        assert exc.error_details.details == {"param": "value"}
        assert exc.error_details.context == {"module": "test"}
        assert exc.error_details.suggestions == ["Check configuration"]

    def test_base_exception_with_cause(self) -> None:
        """Test exception with underlying cause."""
        original_error = ValueError("Original error")
        exc = JPYBaseException(
            error_code="BASE_003",
            message="Exception with cause",
            cause=original_error,
        )

        assert exc.cause == original_error

    def test_exception_repr(self) -> None:
        """Test exception __repr__ method."""
        exc = JPYBaseException(error_code="BASE_004", message="Repr test")

        repr_str = repr(exc)
        assert "JPYBaseException" in repr_str
        assert "BASE_004" in repr_str
        assert "Repr test" in repr_str

    def test_exception_to_dict(self) -> None:
        """Test exception conversion to dictionary."""
        exc = JPYBaseException(
            error_code="BASE_005",
            message="Dict conversion test",
        )

        result = exc.to_dict()
        assert result["error_code"] == "BASE_005"
        assert result["message"] == "Dict conversion test"
        assert result["exception_type"] == "JPYBaseException"
        assert "timestamp" in result

    def test_exception_to_dict_with_cause(self) -> None:
        """Test exception to_dict with traceback."""
        try:
            raise ValueError("Original error")
        except ValueError as e:
            exc = JPYBaseException(
                error_code="BASE_006",
                message="Exception with traceback",
                cause=e,
            )

            result = exc.to_dict()
            assert result["traceback"] is not None
            assert "ValueError" in result["traceback"]

    def test_exception_to_json(self) -> None:
        """Test exception JSON serialization."""
        exc = JPYBaseException(error_code="BASE_007", message="JSON test")

        json_str = exc.to_json()
        data = json.loads(json_str)
        assert data["error_code"] == "BASE_007"
        assert data["message"] == "JSON test"

    def test_exception_from_dict(self) -> None:
        """Test creating exception from dictionary."""
        data = {
            "error_code": "BASE_008",
            "message": "From dict test",
            "details": {"key": "value"},
        }

        exc = JPYBaseException.from_dict(data)
        assert exc.error_details.error_code == "BASE_008"
        assert exc.error_details.message == "From dict test"
        assert exc.error_details.details == {"key": "value"}

    def test_exception_from_dict_minimal(self) -> None:
        """Test creating exception from minimal dictionary."""
        data = {"error_code": "BASE_009", "message": "Minimal dict test"}

        exc = JPYBaseException.from_dict(data)
        assert exc.error_details.error_code == "BASE_009"
        assert exc.error_details.message == "Minimal dict test"


class TestJPYConfigurationError:
    """Test JPYConfigurationError specific functionality."""

    def test_configuration_error_basic(self) -> None:
        """Test basic JPYConfigurationError creation."""
        exc = JPYConfigurationError(message="Invalid configuration")

        assert exc.error_details.error_code == "CONFIGURATION_ERROR"
        assert exc.error_details.message == "Invalid configuration"
        assert exc.error_details.suggestions is not None
        assert len(exc.error_details.suggestions) > 0

    def test_configuration_error_with_details(self) -> None:
        """Test JPYConfigurationError with detailed parameters."""
        exc = JPYConfigurationError(
            message="Invalid configuration",
            config_key="database.host",
            config_value="invalid_host",
            expected_type=str,
        )

        assert exc.error_details.error_code == "CONFIGURATION_ERROR"
        assert exc.error_details.details is not None
        assert exc.error_details.details["config_key"] == "database.host"
        assert exc.error_details.details["config_value"] == "invalid_host"
        assert exc.error_details.details["expected_type"] == "str"

    def test_configuration_error_with_none_parameters(self) -> None:
        """Test JPYConfigurationError with None parameters."""
        exc = JPYConfigurationError(
            message="Config error with none params",
            config_key=None,
            config_value=None,
            expected_type=None,
        )

        assert exc.error_details.error_code == "CONFIGURATION_ERROR"
        assert exc.error_details.details is not None
        assert "config_key" not in exc.error_details.details
        assert "config_value" not in exc.error_details.details
        assert "expected_type" not in exc.error_details.details

    def test_configuration_error_with_zero_value(self) -> None:
        """Test JPYConfigurationError with config_value=0."""
        exc = JPYConfigurationError(
            message="Config error with zero value",
            config_key="port",
            config_value=0,
            expected_type=int,
        )

        assert exc.error_details.error_code == "CONFIGURATION_ERROR"
        assert exc.error_details.details is not None
        assert exc.error_details.details["config_key"] == "port"
        assert exc.error_details.details["config_value"] == "0"
        assert exc.error_details.details["expected_type"] == "int"


class TestJPYCacheError:
    """Test JPYCacheError specific functionality."""

    def test_cache_error_basic(self) -> None:
        """Test basic JPYCacheError creation."""
        exc = JPYCacheError(message="Cache operation failed")

        assert exc.error_details.error_code == "CACHE_ERROR"
        assert exc.error_details.message == "Cache operation failed"
        assert exc.error_details.suggestions is not None
        assert len(exc.error_details.suggestions) > 0

    def test_cache_error_with_details(self) -> None:
        """Test JPYCacheError with detailed parameters."""
        exc = JPYCacheError(
            message="Cache operation failed",
            cache_key="user:123",
            cache_backend="redis",
            operation="get",
        )

        assert exc.error_details.error_code == "CACHE_ERROR"
        assert exc.error_details.details is not None
        assert exc.error_details.details["cache_key"] == "user:123"
        assert exc.error_details.details["cache_backend"] == "redis"
        assert exc.error_details.details["operation"] == "get"

    def test_cache_error_with_none_parameters(self) -> None:
        """Test JPYCacheError with None parameters."""
        exc = JPYCacheError(
            message="Cache error with none params",
            cache_key=None,
            cache_backend=None,
            operation=None,
        )

        assert exc.error_details.error_code == "CACHE_ERROR"
        assert exc.error_details.details is not None
        assert "cache_key" not in exc.error_details.details
        assert "cache_backend" not in exc.error_details.details
        assert "operation" not in exc.error_details.details

    def test_cache_error_custom_suggestions_override(self) -> None:
        """Test that custom suggestions override defaults."""
        custom_suggestions = ["Custom suggestion 1", "Custom suggestion 2"]
        exc = JPYCacheError(
            message="Cache error",
            suggestions=custom_suggestions,
        )

        assert exc.error_details.suggestions == custom_suggestions


class TestJPYDatabaseError:
    """Test JPYDatabaseError specific functionality."""

    def test_database_error_basic(self) -> None:
        """Test basic JPYDatabaseError creation."""
        exc = JPYDatabaseError(message="Database query failed")

        assert exc.error_details.error_code == "DATABASE_ERROR"
        assert exc.error_details.message == "Database query failed"
        assert exc.error_details.suggestions is not None
        assert len(exc.error_details.suggestions) > 0

    def test_database_error_with_details(self) -> None:
        """Test JPYDatabaseError with detailed parameters."""
        exc = JPYDatabaseError(
            message="Database query failed",
            table_name="users",
            operation="select",
            query="SELECT * FROM users",
        )

        assert exc.error_details.error_code == "DATABASE_ERROR"
        assert exc.error_details.details is not None
        assert exc.error_details.details["table_name"] == "users"
        assert exc.error_details.details["operation"] == "select"
        assert exc.error_details.details["query"] == "SELECT * FROM users"

    def test_database_error_with_none_parameters(self) -> None:
        """Test JPYDatabaseError with None parameters."""
        exc = JPYDatabaseError(
            message="Database error with none params",
            table_name=None,
            operation=None,
            query=None,
        )

        assert exc.error_details.error_code == "DATABASE_ERROR"
        assert exc.error_details.details is not None
        assert "table_name" not in exc.error_details.details
        assert "operation" not in exc.error_details.details
        assert "query" not in exc.error_details.details


class TestJPYValidationError:
    """Test JPYValidationError specific functionality."""

    def test_validation_error_basic(self) -> None:
        """Test basic JPYValidationError creation."""
        exc = JPYValidationError(message="Field validation failed")

        assert exc.error_details.error_code == "VALIDATION_ERROR"
        assert exc.error_details.message == "Field validation failed"
        assert exc.error_details.suggestions is not None
        assert len(exc.error_details.suggestions) > 0

    def test_validation_error_with_details(self) -> None:
        """Test JPYValidationError with detailed parameters."""
        exc = JPYValidationError(
            message="Field validation failed",
            field_name="email",
            field_value="invalid-email",
            validation_rule="email_format",
        )

        assert exc.error_details.error_code == "VALIDATION_ERROR"
        assert exc.error_details.details is not None
        assert exc.error_details.details["field_name"] == "email"
        assert exc.error_details.details["field_value"] == "invalid-email"
        assert exc.error_details.details["validation_rule"] == "email_format"

    def test_validation_error_with_none_parameters(self) -> None:
        """Test JPYValidationError with None parameters."""
        exc = JPYValidationError(
            message="Validation error with none params",
            field_name=None,
            field_value=None,
            validation_rule=None,
        )

        assert exc.error_details.error_code == "VALIDATION_ERROR"
        assert exc.error_details.details is not None
        assert "field_name" not in exc.error_details.details
        assert "field_value" not in exc.error_details.details
        assert "validation_rule" not in exc.error_details.details

    def test_validation_error_with_zero_value(self) -> None:
        """Test JPYValidationError with field_value=0."""
        exc = JPYValidationError(
            message="Validation error with zero value",
            field_name="count",
            field_value=0,
            validation_rule="positive_number",
        )

        assert exc.error_details.error_code == "VALIDATION_ERROR"
        assert exc.error_details.details is not None
        assert exc.error_details.details["field_name"] == "count"
        assert exc.error_details.details["field_value"] == "0"
        assert exc.error_details.details["validation_rule"] == "positive_number"


class TestJPYLoggingError:
    """Test JPYLoggingError specific functionality."""

    def test_logging_error_basic(self) -> None:
        """Test basic JPYLoggingError creation."""
        exc = JPYLoggingError(message="Logging setup failed")

        assert exc.error_details.error_code == "LOGGING_ERROR"
        assert exc.error_details.message == "Logging setup failed"
        assert exc.error_details.suggestions is not None
        assert len(exc.error_details.suggestions) > 0

    def test_logging_error_with_details(self) -> None:
        """Test JPYLoggingError with detailed parameters."""
        exc = JPYLoggingError(
            message="Logging setup failed",
            logger_name="app.cache",
            log_level="DEBUG",
            handler_type="FileHandler",
            context={"log_file": "/var/log/app.log"},
        )

        assert exc.error_details.error_code == "LOGGING_ERROR"
        assert exc.error_details.details is not None
        assert exc.error_details.details["logger_name"] == "app.cache"
        assert exc.error_details.details["log_level"] == "DEBUG"
        assert exc.error_details.details["handler_type"] == "FileHandler"
        assert exc.error_details.context is not None
        assert exc.error_details.context["log_file"] == "/var/log/app.log"

    def test_logging_error_with_none_parameters(self) -> None:
        """Test JPYLoggingError with None parameters."""
        exc = JPYLoggingError(
            message="Logging error with none params",
            logger_name=None,
            log_level=None,
            handler_type=None,
        )

        assert exc.error_details.error_code == "LOGGING_ERROR"
        assert exc.error_details.message == "Logging error with none params"
        assert exc.error_details.details is not None
        assert "logger_name" not in exc.error_details.details
        assert "log_level" not in exc.error_details.details
        assert "handler_type" not in exc.error_details.details


class TestJPYConnectionError:
    """Test JPYConnectionError specific functionality."""

    def test_connection_error_basic(self) -> None:
        """Test basic JPYConnectionError creation."""
        exc = JPYConnectionError(message="Connection failed")

        assert exc.error_details.error_code == "CONNECTION_ERROR"
        assert exc.error_details.message == "Connection failed"
        assert exc.error_details.suggestions is not None
        assert len(exc.error_details.suggestions) > 0

    def test_connection_error_with_details(self) -> None:
        """Test JPYConnectionError with detailed parameters."""
        exc = JPYConnectionError(
            message="Connection failed",
            service_name="redis",
            host="localhost",
            port=6379,
            context={"timeout": 30},
        )

        assert exc.error_details.error_code == "CONNECTION_ERROR"
        assert exc.error_details.details is not None
        assert exc.error_details.details["service_name"] == "redis"
        assert exc.error_details.details["host"] == "localhost"
        assert exc.error_details.details["port"] == 6379
        assert exc.error_details.context is not None
        assert exc.error_details.context["timeout"] == 30

    def test_connection_error_with_none_parameters(self) -> None:
        """Test JPYConnectionError with None parameters."""
        exc = JPYConnectionError(
            message="Connection error with none params",
            service_name=None,
            host=None,
            port=None,
        )

        assert exc.error_details.error_code == "CONNECTION_ERROR"
        assert exc.error_details.message == "Connection error with none params"
        assert exc.error_details.details is not None
        assert "service_name" not in exc.error_details.details
        assert "host" not in exc.error_details.details
        assert "port" not in exc.error_details.details


class TestExceptionRegistry:
    """Test exception registry and factory functionality."""

    def test_get_exception_class_known(self) -> None:
        """Test getting known exception class."""
        cls = ExceptionRegistry.get_exception_class("CACHE_ERROR")
        assert cls == JPYCacheError

    def test_get_exception_class_unknown(self) -> None:
        """Test getting unknown exception class returns base."""
        cls = ExceptionRegistry.get_exception_class("NON_EXISTENT")
        assert cls == JPYBaseException

    def test_create_exception_by_code(self) -> None:
        """Test creating exception using registry."""
        exc = create_exception(
            "CACHE_ERROR",
            "Cache test error",
            cache_key="test:key",
        )

        assert isinstance(exc, JPYCacheError)
        assert exc.error_details.error_code == "CACHE_ERROR"
        assert exc.error_details.message == "Cache test error"

    def test_unknown_error_code(self) -> None:
        """Test handling unknown error code."""
        exc = create_exception("UNKNOWN_ERROR", "Unknown error")
        assert isinstance(exc, JPYBaseException)
        assert not isinstance(exc, JPYCacheError)

    def test_list_error_codes(self) -> None:
        """Test listing all registered error codes."""
        codes = ExceptionRegistry.list_error_codes()
        expected_codes = [
            "CONFIGURATION_ERROR",
            "CACHE_ERROR",
            "DATABASE_ERROR",
            "LOGGING_ERROR",
            "VALIDATION_ERROR",
            "CONNECTION_ERROR",
        ]

        for code in expected_codes:
            assert code in codes

    def test_register_new_exception(self) -> None:
        """Test registering a new exception type."""

        class CustomException(JPYBaseException):
            def __init__(self, message: str, **kwargs: Any) -> None:
                super().__init__(
                    error_code="CUSTOM_ERROR",
                    message=message,
                    **kwargs,
                )

        register_exception("CUSTOM_ERROR", CustomException)

        # Test that it's registered
        assert "CUSTOM_ERROR" in ExceptionRegistry.list_error_codes()

        # Test creation
        exc = create_exception("CUSTOM_ERROR", "Custom error message")
        assert isinstance(exc, CustomException)
        assert exc.error_details.error_code == "CUSTOM_ERROR"

    def test_create_all_exception_types(self) -> None:
        """Test creating all registered exception types."""
        error_codes = [
            "CONFIGURATION_ERROR",
            "CACHE_ERROR",
            "DATABASE_ERROR",
            "LOGGING_ERROR",
            "VALIDATION_ERROR",
            "CONNECTION_ERROR",
        ]

        for error_code in error_codes:
            exc = create_exception(error_code, f"Test {error_code}")
            assert exc.error_details.error_code == error_code
            assert f"Test {error_code}" in exc.error_details.message

    def test_exception_inheritance(self) -> None:
        """Test that all specific exceptions inherit from base."""
        exceptions = [
            JPYConfigurationError("test"),
            JPYCacheError("test"),
            JPYDatabaseError("test"),
            JPYLoggingError("test"),
            JPYValidationError("test"),
            JPYConnectionError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, JPYBaseException)
            assert isinstance(exc, Exception)


class TestEdgeCasesAndIntegration:
    """Test edge cases, integration scenarios, and complex use cases."""

    def test_exception_with_none_values(self) -> None:
        """Test exception creation with None values."""
        exc = JPYBaseException(
            error_code="TEST_001",
            message="Test message",
            details=None,
            context=None,
            suggestions=None,
        )

        assert exc.error_details.details == {}
        assert exc.error_details.context == {}
        assert exc.error_details.suggestions == []

    def test_exception_with_empty_collections(self) -> None:
        """Test exception with empty details and suggestions."""
        exc = JPYBaseException(
            error_code="TEST_002",
            message="Test message",
            details={},
            context={},
            suggestions=[],
        )

        assert exc.error_details.details == {}
        assert exc.error_details.context == {}
        assert exc.error_details.suggestions == []

    def test_complex_details_serialization(self) -> None:
        """Test serialization with complex data types."""
        exc = JPYBaseException(
            error_code="TEST_003",
            message="Complex data test",
            details={
                "list": [1, 2, 3],
                "nested": {"key": "value"},
                "number": 42,
                "boolean": True,
            },
        )

        json_str = exc.to_json()
        data = json.loads(json_str)
        assert data["details"]["list"] == [1, 2, 3]
        assert data["details"]["nested"]["key"] == "value"
        assert data["details"]["number"] == 42
        assert data["details"]["boolean"] is True

    def test_exception_chaining(self) -> None:
        """Test exception chaining behavior."""
        original = ValueError("Original error")

        try:
            raise original
        except ValueError:
            exc = JPYBaseException(
                error_code="CHAINED_001",
                message="Chained exception",
                cause=original,
            )

            assert exc.cause == original
            # We don't set __cause__ automatically
            assert exc.__cause__ is None
