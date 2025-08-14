# Logger — Concepts and API

This document introduces the logging module: configuration, core classes, and
backends. All public APIs are type‑annotated and tested.

## Concepts

- **Global Config**: `GlobalLoggerConfig` — app‑level defaults, default
  backends, and safety limits (sanitization, context size, async queue size).
- **Logger**: `Logger` — per‑component logger; supports sync and async logging.
- **Backends**: `ConsoleBackend`, `FileBackend`, `RestApiBackend`,
  `WebSocketBackend` — created by `BackendFactory`.
- **Exceptions**: rich error details with stable error codes.

## Core Classes

### LoggerManager

- Singleton manager of global configuration and logger instances
- `set_global_config(config: GlobalLoggerConfig) -> None`
- `get_logger(name: str, config: LoggerConfig | None = None, *, force_new=False) -> Logger`
- `shutdown_all() -> None` — schedules safe shutdown for all loggers

### Logger

- Sync API: `trace`, `debug`, `info`, `warning`, `error`, `critical`
- Async API: `atrace`, `adebug`, `ainfo`, `awarning`, `aerror`, `acritical`
- Contexts: `context(**kv)`, `acontext(**kv)` add temporary fields
- Composition: `bind(**kv)` returns a child logger with persistent context
- Maintenance: `flush()`, `close()`, `get_stats()`, `get_backend_stats()`

```python
from jinpy_utils.logger.core import Logger
log = Logger.get_logger("app")
log.info("hello", {"env": "dev"})
```

### Configuration

```python
from pathlib import Path
from jinpy_utils.logger.config import (
    GlobalLoggerConfig,
    LoggerConfig,
    ConsoleBackendConfig,
    FileBackendConfig,
)

cfg = GlobalLoggerConfig(
    backends=[
        ConsoleBackendConfig(name="console"),
        FileBackendConfig(name="file", file_path=Path("logs/app.log")),
    ]
)
```

### Backends

Backends implement `BackendInterface` and are created by `BackendFactory`.

- `ConsoleBackend` — fast TTY output with optional colors and console format
- `FileBackend` — append‑only file writes with async batching and rotation hooks
- `RestApiBackend` — batches to HTTP endpoint with security headers
- `WebSocketBackend` — real‑time streaming to WS endpoints with reconnect and ping

```python
from jinpy_utils.logger.backends import BackendFactory
from jinpy_utils.logger.config import ConsoleBackendConfig

console = BackendFactory.create_backend(ConsoleBackendConfig(name="console"))
```

## Safety and Performance

- Sanitization: redact keys containing `password`, `token`, `secret`, `key`, `auth`
- Context size limits: prevent oversized payloads
- Async queue: configurable max size; overflow falls back to direct writes
- Performance alerts (optional): triggers when logging cadence is too slow

## Error Model

- `JPYLoggerError`, `JPYLoggerConfigurationError`, `JPYLoggerBackendError`,
  `JPYLoggerConnectionError`, `JPYLoggerWebSocketError`, and more provide
  consistent, serializable error details.

```python
from jinpy_utils.logger.exceptions import JPYLoggerBackendError

try:
    # ... write to backend
    pass
except Exception as exc:
    raise JPYLoggerBackendError("backend failure", backend_type="file") from exc
```
