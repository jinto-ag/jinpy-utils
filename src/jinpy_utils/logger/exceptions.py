"""Custom exceptions for the logger module.

This module defines specific exceptions for logging operations,
extending the base exception system for better error handling.
"""

from typing import Any

from jinpy_utils.base.exceptions import JPYLoggingError


class JPYLoggerError(JPYLoggingError):
    """Base exception for all logger-related errors.

    This extends JPYLoggingError to provide logger-specific error handling
    while maintaining consistency with the base exception system.
    """

    def __init__(
        self,
        message: str,
        logger_name: str | None = None,
        operation: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize logger error."""
        details = kwargs.pop("details", {})
        if logger_name:
            details["logger_name"] = logger_name
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            logger_name=logger_name,
            handler_type=kwargs.pop("handler_type", "Logger"),
            details=details,
            suggestions=kwargs.pop(
                "suggestions",
                [
                    "Check logger configuration",
                    "Verify logging permissions",
                    "Ensure proper initialization",
                ],
            ),
            **kwargs,
        )


class JPYLoggerConfigurationError(JPYLoggingError):
    """Exception raised for logger configuration errors."""

    def __init__(
        self,
        message: str,
        config_section: str | None = None,
        config_value: Any | None = None,
        logger_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize configuration error."""
        details = kwargs.pop("details", {})
        if config_section:
            details["config_section"] = config_section
        if config_value is not None:
            details["config_value"] = str(config_value)

        super().__init__(
            message=message,
            logger_name=logger_name,
            handler_type="LoggerConfiguration",
            details=details,
            suggestions=kwargs.pop(
                "suggestions",
                [
                    "Check logger configuration syntax",
                    "Verify all required settings",
                    "Ensure valid configuration values",
                ],
            ),
            **kwargs,
        )


class JPYLoggerBackendError(JPYLoggingError):
    """Exception raised for backend-specific errors."""

    def __init__(
        self,
        message: str,
        backend_type: str | None = None,
        backend_config: dict[str, Any] | None = None,
        logger_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize backend error."""
        details = kwargs.pop("details", {})
        if backend_type:
            details["backend_type"] = backend_type
        if backend_config:
            details["backend_config"] = backend_config

        super().__init__(
            message=message,
            logger_name=logger_name,
            handler_type=(
                f"LoggerBackend:{backend_type}" if backend_type else "LoggerBackend"
            ),
            details=details,
            suggestions=kwargs.pop(
                "suggestions",
                [
                    "Check backend connectivity",
                    "Verify backend configuration",
                    "Ensure backend dependencies are installed",
                ],
            ),
            **kwargs,
        )


class JPYLoggerConnectionError(JPYLoggingError):
    """Exception raised for connection-related errors."""

    def __init__(
        self,
        message: str,
        endpoint: str | None = None,
        connection_type: str | None = None,
        logger_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize connection error."""
        details = kwargs.pop("details", {})
        if endpoint:
            details["endpoint"] = endpoint
        if connection_type:
            details["connection_type"] = connection_type

        super().__init__(
            message=message,
            logger_name=logger_name,
            handler_type=(
                f"LoggerConnection:{connection_type}"
                if connection_type
                else "LoggerConnection"
            ),
            details=details,
            suggestions=kwargs.pop(
                "suggestions",
                [
                    "Check network connectivity",
                    "Verify endpoint availability",
                    "Check firewall settings",
                    "Validate authentication credentials",
                ],
            ),
            **kwargs,
        )


class JPYLoggerSecurityError(JPYLoggingError):
    """Exception raised for security-related errors."""

    def __init__(
        self,
        message: str,
        security_context: str | None = None,
        logger_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize security error."""
        details = kwargs.pop("details", {})
        if security_context:
            details["security_context"] = security_context

        super().__init__(
            message=message,
            logger_name=logger_name,
            handler_type="LoggerSecurity",
            details=details,
            suggestions=kwargs.pop(
                "suggestions",
                [
                    "Check authentication credentials",
                    "Verify API key permissions",
                    "Ensure secure connection",
                    "Review security policies",
                ],
            ),
            **kwargs,
        )


class JPYLoggerPerformanceError(JPYLoggingError):
    """Exception raised for performance-related errors."""

    def __init__(
        self,
        message: str,
        performance_metric: str | None = None,
        threshold_value: float | None = None,
        actual_value: float | None = None,
        logger_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize performance error."""
        details = kwargs.pop("details", {})
        if performance_metric:
            details["performance_metric"] = performance_metric
        if threshold_value is not None:
            details["threshold_value"] = threshold_value
        if actual_value is not None:
            details["actual_value"] = actual_value

        super().__init__(
            message=message,
            logger_name=logger_name,
            handler_type="LoggerPerformance",
            details=details,
            suggestions=kwargs.pop(
                "suggestions",
                [
                    "Increase buffer sizes",
                    "Reduce log frequency",
                    "Optimize backend configuration",
                    "Scale backend resources",
                ],
            ),
            **kwargs,
        )


class JPYLoggerWebSocketError(JPYLoggingError):
    """Exception raised for WebSocket-related errors."""

    def __init__(
        self,
        message: str,
        ws_endpoint: str | None = None,
        ws_state: str | None = None,
        logger_name: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize WebSocket error."""
        details = kwargs.pop("details", {})
        if ws_endpoint:
            details["ws_endpoint"] = ws_endpoint
        if ws_state:
            details["ws_state"] = ws_state

        super().__init__(
            message=message,
            logger_name=logger_name,
            handler_type="LoggerWebSocket",
            details=details,
            suggestions=kwargs.pop(
                "suggestions",
                [
                    "Check WebSocket endpoint availability",
                    "Verify WebSocket connection state",
                    "Check network connectivity",
                    "Review WebSocket authentication",
                ],
            ),
            **kwargs,
        )
