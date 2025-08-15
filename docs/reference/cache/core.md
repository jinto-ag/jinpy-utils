# Cache Core API

Core cache classes and helper functions providing synchronous and asynchronous APIs, a singleton-aware manager, and context helpers.

## Factory Functions

### get_cache

::: jinpy_utils.cache.get_cache
    options:
      show_source: true
      show_signature_annotations: true

### get_cache_manager

::: jinpy_utils.cache.get_cache_manager
    options:
      show_source: true
      show_signature_annotations: true

## Core Classes

### CacheManager

::: jinpy_utils.cache.CacheManager
    options:
      show_root_heading: true
      show_root_toc_entry: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      members:
        - __init__
        - get_backend
        - get
        - set
        - delete
        - exists
        - clear
        - get_many
        - set_many
        - delete_many
        - incr
        - decr
        - ttl
        - touch
        - is_healthy
        - close
        - aget
        - aset
        - adelete
        - aexists
        - aclear
        - aget_many
        - aset_many
        - adelete_many
        - aincr
        - adecr
        - attl
        - atouch
        - ais_healthy
        - aclose
        - using
        - ausing

### Cache

::: jinpy_utils.cache.Cache
    options:
      show_root_heading: true
      show_root_toc_entry: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      members:
        - __init__
        - get
        - set
        - delete
        - exists
        - clear
        - get_many
        - set_many
        - delete_many
        - incr
        - decr
        - ttl
        - touch
        - is_healthy
        - close
        - aget
        - aset
        - adelete
        - aexists
        - aclear
        - aget_many
        - aset_many
        - adelete_many
        - aincr
        - adecr
        - attl
        - atouch
        - ais_healthy
        - aclose

### CacheClient

::: jinpy_utils.cache.CacheClient
    options:
      show_source: true
      show_signature_annotations: true

### AsyncCacheClient

::: jinpy_utils.cache.AsyncCacheClient
    options:
      show_source: true
      show_signature_annotations: true

## Interfaces

### CacheInterface

::: jinpy_utils.cache.CacheInterface
    options:
      show_source: true
      show_signature_annotations: true

### AsyncCacheInterface

::: jinpy_utils.cache.AsyncCacheInterface
    options:
      show_source: true
      show_signature_annotations: true

## Utilities

### normalize_key

::: jinpy_utils.cache.utils.normalize_key
    options:
      show_source: true
      show_signature_annotations: true

### compute_expiry

::: jinpy_utils.cache.utils.compute_expiry
    options:
      show_source: true
      show_signature_annotations: true

### remaining_ttl

::: jinpy_utils.cache.utils.remaining_ttl
    options:
      show_source: true
      show_signature_annotations: true

### default_serializer

::: jinpy_utils.cache.utils.default_serializer
    options:
      show_source: true
      show_signature_annotations: true

## Examples

### Basic Usage (in-memory)

```python
from jinpy_utils.cache import get_cache

cache = get_cache()  # default in-memory backend
cache.set("user:123", {"name": "Ada"}, ttl=60)
print(cache.get("user:123"))  # {"name": "Ada"}
```

### Async Usage

```python
import asyncio
from jinpy_utils.cache import get_cache

async def main():
    cache = get_cache()
    await cache.aset("token", "abc", ttl=10)
    value = await cache.aget("token")
    print(value)

asyncio.run(main())
```

### Using a context client bound to a backend

```python
from jinpy_utils.cache import CacheManager, MemoryCacheConfig

manager = CacheManager()
# Ensure a named memory backend exists (defaults will be auto-provisioned)
with manager.using("default_memory") as c:
    c.set("k", 1)
    assert c.incr("k") == 2
```

### Reconfiguring the manager with multiple backends

```python
from pathlib import Path
from jinpy_utils.cache import (
    CacheManager, CacheManagerConfig,
    MemoryCacheConfig, FileCacheConfig
)

config = CacheManagerConfig(
    default_backend="mem",
    backends=[
        MemoryCacheConfig(name="mem", default_ttl=120),
        FileCacheConfig(name="disk", directory=Path(".cache"))
    ]
)

manager = CacheManager(config)  # initializes both

# Use the file backend via high-level facade
from jinpy_utils.cache import Cache
file_cache = Cache(backend="disk")
file_cache.set("report", {"ok": True})
```

### Atomic counters with TTL

```python
from jinpy_utils.cache import get_cache

cache = get_cache()
count = cache.incr("jobs:completed", amount=1, ttl=300)
```