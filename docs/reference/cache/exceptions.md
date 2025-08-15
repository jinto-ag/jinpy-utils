# Cache Exceptions API

Exception classes specific to the cache module with structured error metadata.

## Base Cache Exception

### CacheException

::: jinpy_utils.cache.CacheException
    options:
      show_source: true
      show_signature_annotations: true

## Specific Cache Exceptions

### CacheConfigurationError

::: jinpy_utils.cache.CacheConfigurationError
    options:
      show_source: true
      show_signature_annotations: true

### CacheConnectionError

::: jinpy_utils.cache.CacheConnectionError
    options:
      show_source: true
      show_signature_annotations: true

### CacheSerializationError

::: jinpy_utils.cache.CacheSerializationError
    options:
      show_source: true
      show_signature_annotations: true

### CacheKeyError

::: jinpy_utils.cache.CacheKeyError
    options:
      show_source: true
      show_signature_annotations: true

### CacheTimeoutError

::: jinpy_utils.cache.CacheTimeoutError
    options:
      show_source: true
      show_signature_annotations: true

### CacheBackendError

::: jinpy_utils.cache.CacheBackendError
    options:
      show_source: true
      show_signature_annotations: true

## Usage Examples

### Handling configuration errors

```python
from jinpy_utils.cache import CacheManager, CacheManagerConfig, CacheConfigurationError

try:
    CacheManager(CacheManagerConfig(backends=[]))
except CacheConfigurationError as e:
    print("Config error:", e.message)
```

### Handling backend errors

```python
from jinpy_utils.cache import Cache, CacheBackendError

cache = Cache()
try:
    cache.set("k", object())  # may fail for selected serializer
except CacheBackendError as e:
    print("Backend error:", e.message)
```