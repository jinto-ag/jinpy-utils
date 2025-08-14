"""Base exception types and helpers for jinpy-utils.

This package provides a structured, Pydantic-backed exception hierarchy and a
registry for creating and managing errors in a consistent way across the
library.
"""

from jinpy_utils.base.exceptions import (
    ErrorDetails,
    ExceptionRegistry,
    JPYBaseException,
    JPYCacheError,
    JPYConfigurationError,
    JPYConnectionError,
    JPYDatabaseError,
    JPYLoggingError,
    JPYValidationError,
    create_exception,
    register_exception,
)

__all__ = [
    "ErrorDetails",
    "ExceptionRegistry",
    "JPYBaseException",
    "JPYCacheError",
    "JPYConfigurationError",
    "JPYConnectionError",
    "JPYDatabaseError",
    "JPYLoggingError",
    "JPYValidationError",
    "create_exception",
    "register_exception",
]
