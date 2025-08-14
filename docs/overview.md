# JPY-Utils — Overview

> Status: alpha (v0.1.0-alpha-2)

JPY-Utils is a set of focused utilities for Python applications, with an initial
emphasis on a modern, type-safe logging system. The library follows SOLID
principles, 12‑factor design, and PEP 8. It is rigorously linted (ruff/flake8)
and type-checked (mypy) and ships with high test coverage.

## Highlights

- Type‑safe, structured logging with configurable backends
- Pydantic‑based configuration models with validation
- First‑party support for async and sync I/O
- Consistent, structured error model across modules
- Production‑ready defaults and ergonomics

## Architecture at a Glance

- `logger/core.py` — High‑performance `Logger`, `LoggerManager`, convenience
  helpers, and async processing queue
- `logger/backends.py` — Console, File, REST API, and WebSocket backends
  following an explicit `BackendInterface`
- `logger/config.py` — Strongly typed Pydantic models for configuration
  (global, per‑logger, per‑backend)
- `logger/exceptions.py` and `base/exceptions.py` — Structured exceptions with
  a consistent payload (error code, details, suggestions, timestamps)

## Design Principles

- **Single Responsibility** — each backend implements one transport concern
- **Open/Closed** — new backends can be added via `BackendFactory.register_backend`
- **Interface Segregation** — `BackendInterface` is focused and stable
- **12‑Factor** — environment‑driven config (`GlobalLoggerConfig.from_env`) and
  append‑only logging
- **Safety** — strict mypy, ruff linters, and comprehensive tests

## When to Use

- You need structured logs with multiple outputs
- You want a type‑safe configuration and predictable behavior under load
- You prefer explicit async control and graceful shutdown semantics

See also:

- [Getting Started](./getting-started.md)
- [Logger: Concepts and API](./logger.md)
- [Base Exceptions](./base.md)
