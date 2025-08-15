"""
Public API for the jinpy-utils cache package.

This module exposes the primary cache classes, configuration models, enums,
exceptions, interfaces, and factory/helpers for ergonomic imports.

Example:
    from jinpy_utils.cache import (
        Cache, CacheManager, CacheManagerConfig, CacheBackendType,
        get_cache, get_cache_manager,
    )
"""

from jinpy_utils.cache.backends import CacheBackendFactory
from jinpy_utils.cache.config import (
    BaseCacheBackendConfig,
    CacheManagerConfig,
    FileCacheConfig,
    MemoryCacheConfig,
    RedisCacheConfig,
)
from jinpy_utils.cache.core import (
    AsyncCacheClient,
    Cache,
    CacheClient,
    CacheManager,
    get_cache,
    get_cache_manager,
)
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
from jinpy_utils.cache.interfaces import AsyncCacheInterface, CacheInterface

__all__: list[str] = [
    "AsyncCacheClient",
    "AsyncCacheInterface",
    "BaseCacheBackendConfig",
    "Cache",
    "CacheBackendError",
    "CacheBackendFactory",
    "CacheBackendType",
    "CacheClient",
    "CacheConfigurationError",
    "CacheConnectionError",
    "CacheErrorType",
    "CacheException",
    "CacheInterface",
    "CacheKeyError",
    "CacheManager",
    "CacheManagerConfig",
    "CacheOperation",
    "CacheSerializationError",
    "CacheTimeoutError",
    "FileCacheConfig",
    "MemoryCacheConfig",
    "RedisCacheConfig",
    "get_cache",
    "get_cache_manager",
]
