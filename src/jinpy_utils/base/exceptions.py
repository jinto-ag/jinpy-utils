"""Exception classes for jinpy-utils library.

This module provides a hierarchy of exceptions with structured error data
using Pydantic models for type safety and JSON serialization.
"""

import traceback
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, Field

from jinpy_utils.utils.timing import get_current_datetime


class ErrorDetails(BaseModel):
    """Pydantic model for structured error information."""

    error_code: str = Field(..., description="Unique error code identifier")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=get_current_datetime,
        description="When the error occurred",
    )
    context: dict[str, Any] | None = Field(
        default=None, description="Context where error occurred"
    )
    suggestions: list[str] | None = Field(
        default=None, description="Suggested solutions"
    )


class JPYBaseException(Exception):
    """Base exception class for all jinpy-utils exceptions.

    This exception provides structured error information using Pydantic models
    and supports JSON serialization for better error handling and logging.

    Args:
        error_code: Unique identifier for the error type
        message: Human-readable error description
        details: Additional structured error information
        context: Context information where error occurred
        suggestions: List of suggested solutions
        cause: Original exception that caused this error
    """

    def __init__(  # noqa: PLR0913
        self,
        error_code: str,
        message: str,
        details: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize the exception with structured error data."""
        self.error_details = ErrorDetails(
            error_code=error_code,
            message=message,
            details=details or {},
            context=context or {},
            suggestions=suggestions or [],
        )
        self.cause = cause
        super().__init__(self.error_details.message)

    def __str__(self) -> str:
        """Return string representation of the exception."""
        return f"[{self.error_details.error_code}] {self.error_details.message}"

    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"{self.__class__.__name__}("
            f"error_code='{self.error_details.error_code}', "
            f"message='{self.error_details.message}'"
            f")"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary format."""
        result: dict[str, Any] = self.error_details.model_dump()
        result.update(
            {
                "exception_type": self.__class__.__name__,
                "traceback": traceback.format_exc() if self.cause else None,
            }
        )
        return result

    def to_json(self) -> str:
        """Convert exception to JSON format."""
        return str(self.error_details.model_dump_json())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JPYBaseException":
        """Create exception instance from dictionary."""
        return cls(
            error_code=data["error_code"],
            message=data["message"],
            details=data.get("details"),
            context=data.get("context"),
            suggestions=data.get("suggestions"),
        )


class JPYConfigurationError(JPYBaseException):
    """Exception raised for configuration-related errors."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_value: Any | None = None,
        expected_type: type | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize configuration error."""
        details = kwargs.pop("details", {})
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = str(config_value)
        if expected_type:
            details["expected_type"] = expected_type.__name__

        super().__init__(
            error_code="CONFIGURATION_ERROR",
            message=message,
            details=details,
            suggestions=kwargs.pop(
                "suggestions",
                [
                    "Check configuration file syntax",
                    "Verify environment variables",
                    "Ensure all required settings are provided",
                ],
            ),
            **kwargs,
        )


class JPYCacheError(JPYBaseException):
    """Exception raised for caching-related errors."""

    def __init__(
        self,
        message: str,
        cache_key: str | None = None,
        cache_backend: str | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize cache error."""
        details = kwargs.pop("details", {})
        if cache_key:
            details["cache_key"] = cache_key
        if cache_backend:
            details["cache_backend"] = cache_backend
        if operation:
            details["operation"] = operation

        super().__init__(
            error_code="CACHE_ERROR",
            message=message,
            details=details,
            suggestions=kwargs.pop(
                "suggestions",
                [
                    "Check cache backend connectivity",
                    "Verify cache key format",
                    "Ensure sufficient memory/storage",
                    "Check cache backend configuration",
                ],
            ),
            **kwargs,
        )


class JPYDatabaseError(JPYBaseException):
    """Exception raised for database/ORM-related errors."""

    def __init__(
        self,
        message: str,
        table_name: str | None = None,
        operation: str | None = None,
        query: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize database error."""
        details = kwargs.pop("details", {})
        if table_name:
            details["table_name"] = table_name
        if operation:
            details["operation"] = operation
        if query:
            details["query"] = query

        super().__init__(
            error_code="DATABASE_ERROR",
            message=message,
            details=details,
            suggestions=kwargs.pop(
                "suggestions",
                [
                    "Check database connection",
                    "Verify table/column names",
                    "Ensure proper database permissions",
                    "Check query syntax",
                ],
            ),
            **kwargs,
        )


class JPYLoggingError(JPYBaseException):
    """Exception raised for logging-related errors."""

    def __init__(
        self,
        message: str,
        logger_name: str | None = None,
        log_level: str | None = None,
        handler_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize logging error."""
        details = kwargs.pop("details", {})
        if logger_name:
            details["logger_name"] = logger_name
        if log_level:
            details["log_level"] = log_level
        if handler_type:
            details["handler_type"] = handler_type

        super().__init__(
            error_code="LOGGING_ERROR",
            message=message,
            details=details,
            suggestions=kwargs.pop(
                "suggestions",
                [
                    "Check log file permissions",
                    "Verify log directory exists",
                    "Ensure proper log level configuration",
                    "Check logging handler configuration",
                ],
            ),
            **kwargs,
        )


class JPYValidationError(JPYBaseException):
    """Exception raised for data validation errors."""

    def __init__(
        self,
        message: str,
        field_name: str | None = None,
        field_value: Any | None = None,
        validation_rule: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize validation error."""
        details = kwargs.pop("details", {})
        if field_name:
            details["field_name"] = field_name
        if field_value is not None:
            details["field_value"] = str(field_value)
        if validation_rule:
            details["validation_rule"] = validation_rule

        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            details=details,
            suggestions=kwargs.pop(
                "suggestions",
                [
                    "Check input data format",
                    "Verify required fields are provided",
                    "Ensure data types match expected format",
                    "Review validation rules",
                ],
            ),
            **kwargs,
        )


class JPYConnectionError(JPYBaseException):
    """Exception raised for connection-related errors."""

    def __init__(
        self,
        message: str,
        service_name: str | None = None,
        host: str | None = None,
        port: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize connection error."""
        details = kwargs.pop("details", {})
        if service_name:
            details["service_name"] = service_name
        if host:
            details["host"] = host
        if port:
            details["port"] = port

        super().__init__(
            error_code="CONNECTION_ERROR",
            message=message,
            details=details,
            suggestions=kwargs.pop(
                "suggestions",
                [
                    "Check network connectivity",
                    "Verify service is running",
                    "Check firewall settings",
                    "Ensure correct host and port",
                ],
            ),
            **kwargs,
        )


# ============================================= #
# Exception Registry
# ============================================= #


class ExceptionRegistry:
    """Registry for managing exception types and their metadata."""

    _exceptions: ClassVar[dict[str, type[JPYBaseException]]] = {
        "CONFIGURATION_ERROR": JPYConfigurationError,
        "CACHE_ERROR": JPYCacheError,
        "DATABASE_ERROR": JPYDatabaseError,
        "LOGGING_ERROR": JPYLoggingError,
        "VALIDATION_ERROR": JPYValidationError,
        "CONNECTION_ERROR": JPYConnectionError,
    }

    @classmethod
    def register(
        cls,
        error_code: str,
        exception_class: type[JPYBaseException],
    ) -> None:
        """Register a new exception type."""
        cls._exceptions[error_code] = exception_class

    @classmethod
    def get_exception_class(cls, error_code: str) -> type[JPYBaseException]:
        """Get exception class by error code."""
        return cls._exceptions.get(error_code, JPYBaseException)

    @classmethod
    def create_exception(
        cls,
        error_code: str,
        message: str,
        **kwargs: Any,
    ) -> JPYBaseException:
        """Factory method to create exception by error code."""
        exception_class = cls.get_exception_class(error_code)

        if exception_class == JPYBaseException:
            return exception_class(
                error_code=error_code,
                message=message,
                **kwargs,
            )

        return exception_class(message=message, **kwargs)

    @classmethod
    def list_error_codes(cls) -> list[str]:
        """List all registered error codes."""
        return list(cls._exceptions.keys())


# Convenience functions
def create_exception(
    error_code: str,
    message: str,
    **kwargs: Any,
) -> JPYBaseException:
    """Create exception using the registry."""
    return ExceptionRegistry.create_exception(error_code, message, **kwargs)


def register_exception(
    error_code: str, exception_class: type[JPYBaseException]
) -> None:
    """Register a new exception type."""
    ExceptionRegistry.register(error_code, exception_class)
