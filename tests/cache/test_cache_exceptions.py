"""Tests for jinpy_utils.cache.exceptions."""

from jinpy_utils.base.exceptions import JPYCacheError
from jinpy_utils.cache.enums import CacheBackendType, CacheErrorType, CacheOperation
from jinpy_utils.cache.exceptions import (
    CacheBackendError,
    CacheConfigurationError,
    CacheConnectionError,
    CacheException,
    CacheKeyError,
    CacheSerializationError,
    CacheTimeoutError,
)


class TestCacheExceptions:
    def test_cache_exception_basic(self) -> None:
        exc = CacheException(
            message="cache failed",
            operation=CacheOperation.GET,
            error_type=CacheErrorType.BACKEND_ERROR,
            cache_key="k",
            backend_name="mem",
            backend_type=CacheBackendType.MEMORY.value,
        )
        assert exc.error_details.error_code == "CACHE_ERROR"
        d = exc.to_dict()
        assert d["exception_type"] == "CacheException"
        assert d["details"]["operation"] == "get"
        assert d["details"]["backend_type"] == "memory"

    def test_configuration_error(self) -> None:
        exc = CacheConfigurationError(
            message="bad cfg", config_section="backends", config_value="x"
        )
        assert exc.error_details.details is not None
        assert exc.error_details.details["config_section"] == "backends"

    def test_connection_serialization_key_timeout_backend_errors(self) -> None:
        assert isinstance(CacheConnectionError("x"), JPYCacheError)
        e = CacheSerializationError("x", cache_key="k")
        assert e.error_details.details is not None
        assert e.error_details.details["cache_key"] == "k"
        e2 = CacheKeyError("x", cache_key="k")
        assert e2.error_details.details is not None
        assert e2.error_details.details["cache_key"] == "k"
        e3 = CacheTimeoutError("x", timeout_seconds=1.0)
        assert e3.error_details.details is not None
        assert e3.error_details.details["timeout_seconds"] == 1.0
        e4 = CacheBackendError("x")
        assert e4.error_details.error_code == "CACHE_ERROR"

    def test_cache_exception_none_params_and_custom_suggestions_and_merge(self) -> None:
        # None parameters should not be added to details and custom suggestions override defaults
        custom = ["one", "two"]
        exc = CacheException(
            message="m",
            operation=None,
            error_type=CacheErrorType.OPERATION,
            suggestions=custom,
        )
        assert exc.error_details.suggestions == custom
        # Merge with existing details provided
        exc2 = CacheException(
            message="m",
            operation=None,
            error_type=CacheErrorType.OPERATION,
            details={"existing": "d"},
        )
        assert exc2.error_details.details is not None
        assert exc2.error_details.details["existing"] == "d"
        assert "operation" not in exc2.error_details.details

    def test_configuration_error_without_value(self) -> None:
        exc = CacheConfigurationError(message="cfg", config_section="s")
        assert exc.error_details.details is not None
        assert exc.error_details.details["config_section"] == "s"
        assert "config_value" not in exc.error_details.details

    def test_timeout_error_without_seconds_and_serialization_without_operation(
        self,
    ) -> None:
        tmo = CacheTimeoutError("t")
        assert tmo.error_details.details is not None
        assert "timeout_seconds" not in tmo.error_details.details
        se = CacheSerializationError("ser", cache_key="k")
        assert se.error_details.details is not None
        assert "operation" not in se.error_details.details
