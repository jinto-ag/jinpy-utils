# Cache Utilities

Helper functions for key normalization, TTL/expiry arithmetic, and serialization.

## Key Utilities

### normalize_key

::: jinpy_utils.cache.utils.normalize_key
    options:
      show_source: true
      show_signature_annotations: true

## Time Utilities

### now_seconds

::: jinpy_utils.cache.utils.now_seconds
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

## Serialization

### default_serializer

::: jinpy_utils.cache.utils.default_serializer
    options:
      show_source: true
      show_signature_annotations: true

## Examples

```python
from jinpy_utils.cache.utils import normalize_key, compute_expiry, remaining_ttl

k = normalize_key("  user:1  ")
exp = compute_expiry(10)
print(remaining_ttl(exp))  # ~10.0 initially
```
