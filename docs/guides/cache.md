# Cache Guide

This guide shows how to use the cache module effectively.

## Quick Start

```python
from jinpy_utils.cache import get_cache

cache = get_cache()  # default: in-memory backend
cache.set("user:1", {"name": "Ada"}, ttl=60)
print(cache.get("user:1"))
```

## Choosing a backend

- Memory — fast, process-local, optional size limits
- File — persistent on disk, simple eviction
- Redis — remote/shared, async-first

## Configure backends

```python
from pathlib import Path
from jinpy_utils.cache import CacheManager, CacheManagerConfig, MemoryCacheConfig, FileCacheConfig

config = CacheManagerConfig(
    default_backend="mem",
    backends=[
        MemoryCacheConfig(name="mem", default_ttl=120),
        FileCacheConfig(name="disk", directory=Path(".cache"))
    ]
)
CacheManager(config)
```

## Async usage (Redis or any async-capable backend)

```python
import asyncio
from jinpy_utils.cache import Cache, CacheManager, CacheManagerConfig, RedisCacheConfig

cfg = CacheManagerConfig(
    default_backend="redis",
    backends=[RedisCacheConfig(name="redis", url="redis://localhost:6379/0")]
)
CacheManager(cfg)

async def main():
    cache = Cache(backend="redis")
    await cache.aset("token", "abc", ttl=30)
    print(await cache.aget("token"))

asyncio.run(main())
```

## Bulk operations

```python
from jinpy_utils.cache import get_cache

cache = get_cache()
cache.set_many({"a": 1, "b": 2}, ttl=10)
print(cache.get_many(["a", "b", "c"]))
cache.delete_many(["a", "b"]) 
```

## Counters with TTL

```python
from jinpy_utils.cache import get_cache

cache = get_cache()
print(cache.incr("jobs:done", amount=2, ttl=300))
print(cache.decr("jobs:running"))
```

## Health and lifecycle

```python
from jinpy_utils.cache import Cache

cache = Cache()
print(cache.is_healthy())
cache.close()
```

## Complete API Reference

- [Core Cache API](../reference/cache/core.md)
- [Backends API](../reference/cache/backends.md)
- [Configuration API](../reference/cache/config.md)
- [Exceptions API](../reference/cache/exceptions.md)
