# Cache Enums

Enumeration types used across the cache package.

## CacheBackendType

::: jinpy_utils.cache.CacheBackendType
    options:
      show_source: true
      show_signature_annotations: true

## CacheOperation

::: jinpy_utils.cache.CacheOperation
    options:
      show_source: true
      show_signature_annotations: true

## CacheErrorType

::: jinpy_utils.cache.CacheErrorType
    options:
      show_source: true
      show_signature_annotations: true

## Examples

```python
from jinpy_utils.cache import CacheBackendType, CacheOperation

if CacheBackendType.MEMORY == CacheBackendType("memory"):
    print("Using memory backend")

print(CacheOperation.GET.value)  # "get"
```