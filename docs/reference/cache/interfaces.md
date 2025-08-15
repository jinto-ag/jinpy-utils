# Cache Interfaces

Abstract interfaces defining sync and async cache operations.

## Synchronous Interface

### CacheInterface

::: jinpy_utils.cache.CacheInterface
    options:
      show_source: true
      show_signature_annotations: true

## Asynchronous Interface

### AsyncCacheInterface

::: jinpy_utils.cache.AsyncCacheInterface
    options:
      show_source: true
      show_signature_annotations: true

## Notes

These interfaces define the contract implemented by concrete backends such as in-memory, file, and Redis backends.