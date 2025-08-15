# Cache Backends API

Backend implementations for in-memory, Redis, and file-system storage.

## Backend Base and Factory

### BaseBackend

::: jinpy_utils.cache.backends.BaseBackend
    options:
      show_source: true
      show_signature_annotations: true
      members:
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

### CacheBackendFactory

::: jinpy_utils.cache.CacheBackendFactory
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - create

## In-Memory Backend

### MemoryCacheBackend

::: jinpy_utils.cache.backends.MemoryCacheBackend
    options:
      show_source: true
      show_signature_annotations: true

## Redis Backend

### RedisCacheBackend

::: jinpy_utils.cache.backends.RedisCacheBackend
    options:
      show_source: true
      show_signature_annotations: true

## File Backend

### FileCacheBackend

::: jinpy_utils.cache.backends.FileCacheBackend
    options:
      show_source: true
      show_signature_annotations: true

## Examples

### Memory backend

```python
from jinpy_utils.cache import Cache, MemoryCacheConfig, CacheManagerConfig

config = CacheManagerConfig(backends=[
    MemoryCacheConfig(name="mem", default_ttl=60)
])

cache = Cache(backend="mem")
cache.set("a", 1)
assert cache.get("a") == 1
```

### File backend

```python
from pathlib import Path
from jinpy_utils.cache import Cache, CacheManager, CacheManagerConfig, FileCacheConfig

cfg = CacheManagerConfig(
    default_backend="disk",
    backends=[FileCacheConfig(name="disk", directory=Path(".cache"))]
)
CacheManager(cfg)  # initialize

cache = Cache(backend="disk")
cache.set("report", {"ok": True})
```

### Redis backend

```python
from jinpy_utils.cache import Cache, CacheManager, CacheManagerConfig, RedisCacheConfig

cfg = CacheManagerConfig(
    default_backend="redis",
    backends=[
        RedisCacheConfig(
            name="redis",
            url="redis://localhost:6379/0",
            decode_responses=False,
            pool_size=10,
        )
    ]
)
CacheManager(cfg)  # initialize

cache = Cache(backend="redis")
await cache.aset("k", {"v": 1}, ttl=30)
value = await cache.aget("k")
```
