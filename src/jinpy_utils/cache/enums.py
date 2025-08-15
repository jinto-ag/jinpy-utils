from enum import Enum


class CacheBackendType(str, Enum):
    """Supported cache backend types."""

    MEMORY = "memory"
    REDIS = "redis"
    FILE = "file"


class CacheOperation(str, Enum):
    """Cache operations for context."""

    GET = "get"
    SET = "set"
    DELETE = "delete"
    EXISTS = "exists"
    INCR = "incr"
    DECR = "decr"
    CLEAR = "clear"
    GET_MANY = "get_many"
    SET_MANY = "set_many"
    DELETE_MANY = "delete_many"
    TTL = "ttl"
    TOUCH = "touch"
    CLOSE = "close"
    HEALTH = "health"


class CacheErrorType(str, Enum):
    """Error classifications for cache."""

    CONNECTION = "connection"
    SERIALIZATION = "serialization"
    KEY_ERROR = "key_error"
    TIMEOUT = "timeout"
    BACKEND_ERROR = "backend_error"
    CONFIGURATION = "configuration"
    OPERATION = "operation"
