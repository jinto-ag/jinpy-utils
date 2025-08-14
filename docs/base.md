# Base Exceptions — Overview

The base exception system provides structured error payloads with Pydantic,
backed by stable error codes and suggestions for recovery.

## Error Model

- `ErrorDetails` — Pydantic model with `error_code`, `message`, `details`,
  `context`, `suggestions`, and a timestamp
- `JPYBaseException` — base class exposing `to_dict` and `to_json`

## Derived Exceptions

- `JPYConfigurationError`
- `JPYCacheError`
- `JPYDatabaseError`
- `JPYLoggingError`
- `JPYValidationError`
- `JPYConnectionError`

```python
from jinpy_utils.base.exceptions import JPYConfigurationError

raise JPYConfigurationError(
    message="missing setting",
    config_key="LOGGER_LEVEL",
    expected_type=str,
)
```

## Design Notes

- Consistent remediation guidance via `suggestions`
- JSON‑ready out of the box for API responses and log payloads
- Clear layering: logger‑specific exceptions extend base logging error
