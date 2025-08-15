# Cache Configuration API

Pydantic models defining configuration for cache backends and the cache manager.

## Manager Configuration

### CacheManagerConfig

::: jinpy_utils.cache.CacheManagerConfig
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - __init__

## Backend Configurations

### BaseCacheBackendConfig

::: jinpy_utils.cache.BaseCacheBackendConfig
    options:
      show_source: true
      show_signature_annotations: true

### MemoryCacheConfig

::: jinpy_utils.cache.MemoryCacheConfig
    options:
      show_source: true
      show_signature_annotations: true

### RedisCacheConfig

::: jinpy_utils.cache.RedisCacheConfig
    options:
      show_source: true
      show_signature_annotations: true

### FileCacheConfig

::: jinpy_utils.cache.FileCacheConfig
    options:
      show_source: true
      show_signature_annotations: true

## Examples

### Minimal in-memory config

```python
from jinpy_utils.cache import CacheManager, CacheManagerConfig, MemoryCacheConfig

cfg = CacheManagerConfig(
    default_backend="mem",
    backends=[MemoryCacheConfig(name="mem", default_ttl=30)]
)
CacheManager(cfg)
```

### File backend config

```python
from pathlib import Path
from jinpy_utils.cache import CacheManager, CacheManagerConfig, FileCacheConfig

cfg = CacheManagerConfig(
    default_backend="disk",
    backends=[FileCacheConfig(name="disk", directory=Path(".cache"), file_extension=".bin")]
)
CacheManager(cfg)
```

### Redis backend config

```python
from jinpy_utils.cache import CacheManager, CacheManagerConfig, RedisCacheConfig

cfg = CacheManagerConfig(
    default_backend="redis",
    backends=[RedisCacheConfig(name="redis", url="redis://localhost:6379/0", decode_responses=False)]
)
CacheManager(cfg)
```