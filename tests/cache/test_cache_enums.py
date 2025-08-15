"""Tests for jinpy_utils.cache.enums."""

from jinpy_utils.cache.enums import (
    CacheBackendType,
    CacheErrorType,
    CacheOperation,
)


class TestCacheEnums:
    def test_cache_backend_type_members(self) -> None:
        assert CacheBackendType.MEMORY.value == "memory"
        assert CacheBackendType.REDIS.value == "redis"
        assert CacheBackendType.FILE.value == "file"

    def test_cache_operation_members(self) -> None:
        assert CacheOperation.GET.value == "get"
        assert CacheOperation.SET.value == "set"
        assert CacheOperation.DELETE.value == "delete"
        assert CacheOperation.EXISTS.value == "exists"
        assert CacheOperation.INCR.value == "incr"
        assert CacheOperation.DECR.value == "decr"
        assert CacheOperation.CLEAR.value == "clear"
        assert CacheOperation.GET_MANY.value == "get_many"
        assert CacheOperation.SET_MANY.value == "set_many"
        assert CacheOperation.DELETE_MANY.value == "delete_many"
        assert CacheOperation.TTL.value == "ttl"
        assert CacheOperation.TOUCH.value == "touch"
        assert CacheOperation.CLOSE.value == "close"
        assert CacheOperation.HEALTH.value == "health"

    def test_cache_error_type_members(self) -> None:
        assert CacheErrorType.CONNECTION.value == "connection"
        assert CacheErrorType.SERIALIZATION.value == "serialization"
        assert CacheErrorType.KEY_ERROR.value == "key_error"
        assert CacheErrorType.TIMEOUT.value == "timeout"
        assert CacheErrorType.BACKEND_ERROR.value == "backend_error"
        assert CacheErrorType.CONFIGURATION.value == "configuration"
        assert CacheErrorType.OPERATION.value == "operation"
