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

from typing import List

from .backends import CacheBackendFactory
from .config import (
    BaseCacheBackendConfig,
    CacheManagerConfig,
    FileCacheConfig,
    MemoryCacheConfig,
    RedisCacheConfig,
)
from .core import (
    AsyncCacheClient,
    Cache,
    CacheClient,
    CacheManager,
    get_cache,
    get_cache_manager,
)
from .enums import CacheBackendType, CacheErrorType, CacheOperation
from .exceptions import (
    CacheBackendError,
    CacheConfigurationError,
    CacheConnectionError,
    CacheException,
    CacheKeyError,
    CacheSerializationError,
    CacheTimeoutError,
)
from .interfaces import AsyncCacheInterface, CacheInterface

__all__: List[str] = [
    # Facade and helpers
    "Cache",
    "get_cache",
    "get_cache_manager",
    # Clients
    "CacheClient",
    "AsyncCacheClient",
    # Core
    "CacheManager",
    "CacheBackendFactory",
    # Interfaces
    "CacheInterface",
    "AsyncCacheInterface",
    # Configs
    "BaseCacheBackendConfig",
    "CacheManagerConfig",
    "MemoryCacheConfig",
    "RedisCacheConfig",
    "FileCacheConfig",
    # Enums
    "CacheBackendType",
    "CacheOperation",
    "CacheErrorType",
    # Exceptions
    "CacheException",
    "CacheConfigurationError",
    "CacheConnectionError",
    "CacheSerializationError",
    "CacheKeyError",
    "CacheTimeoutError",
    "CacheBackendError",
]
