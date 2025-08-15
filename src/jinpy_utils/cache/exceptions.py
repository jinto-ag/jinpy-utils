from __future__ import annotations

from typing import Any

from jinpy_utils.base.exceptions import JPYCacheError

from .enums import CacheErrorType, CacheOperation


class CacheException(JPYCacheError):
    """Base cache exception with structured context."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "CACHE_ERROR",
        operation: CacheOperation | None = None,
        error_type: CacheErrorType = CacheErrorType.OPERATION,
        cache_key: str | None = None,
        backend_name: str | None = None,
        backend_type: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if operation:
            details["operation"] = operation.value
        if error_type:
            details["error_type"] = error_type.value
        if cache_key:
            details["cache_key"] = cache_key
        if backend_name:
            details["backend_name"] = backend_name
        if backend_type:
            details["backend_type"] = backend_type

        super().__init__(
            message=message,
            cache_key=cache_key,
            cache_backend=backend_name or backend_type,
            operation=operation.value if operation else None,
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
        self.operation = operation
        self.error_type = error_type
        self.backend_name = backend_name
        self.backend_type = backend_type


class CacheConfigurationError(CacheException):
    """Configuration related cache errors."""

    def __init__(
        self,
        message: str,
        *,
        config_section: str | None = None,
        config_value: str | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if config_section:
            details["config_section"] = config_section
        if config_value is not None:
            details["config_value"] = config_value
        super().__init__(
            message=message,
            error_code="CACHE_CONFIGURATION_ERROR",
            operation=kwargs.pop("operation", None),
            error_type=CacheErrorType.CONFIGURATION,
            details=details,
            **kwargs,
        )


class CacheConnectionError(CacheException):
    """Connection/availability issues with remote cache services."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message=message,
            error_code="CACHE_CONNECTION_ERROR",
            error_type=CacheErrorType.CONNECTION,
            **kwargs,
        )


class CacheSerializationError(CacheException):
    """Serialization/deserialization failures."""

    def __init__(
        self, message: str, *, cache_key: str | None = None, **kwargs: Any
    ) -> None:
        super().__init__(
            message=message,
            error_code="CACHE_SERIALIZATION_ERROR",
            operation=kwargs.pop("operation", None),
            error_type=CacheErrorType.SERIALIZATION,
            cache_key=cache_key,
            **kwargs,
        )


class CacheKeyError(CacheException):
    """Invalid or missing cache key errors."""

    def __init__(
        self, message: str, *, cache_key: str | None = None, **kwargs: Any
    ) -> None:
        super().__init__(
            message=message,
            error_code="CACHE_KEY_ERROR",
            operation=kwargs.pop("operation", None),
            error_type=CacheErrorType.KEY_ERROR,
            cache_key=cache_key,
            **kwargs,
        )


class CacheTimeoutError(CacheException):
    """Cache operation timeouts."""

    def __init__(
        self,
        message: str,
        *,
        timeout_seconds: float | None = None,
        **kwargs: Any,
    ) -> None:
        details = kwargs.pop("details", {})
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(
            message=message,
            error_code="CACHE_TIMEOUT_ERROR",
            operation=kwargs.pop("operation", None),
            error_type=CacheErrorType.TIMEOUT,
            details=details,
            **kwargs,
        )


class CacheBackendError(CacheException):
    """Backend-specific failures."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(
            message=message,
            error_code="CACHE_BACKEND_ERROR",
            error_type=CacheErrorType.BACKEND_ERROR,
            **kwargs,
        )
