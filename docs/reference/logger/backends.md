# Logger Backends API

Backend implementations for different output destinations.

## Backend Interface

### BackendInterface

::: jinpy_utils.logger.BackendInterface
    options:
      show_source: true
      show_signature_annotations: true

### BaseBackend

::: jinpy_utils.logger.BaseBackend
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - __init__
        - handle
        - format_entry
        - should_handle
        - shutdown
        - is_async_enabled

## Console Backend

### ConsoleBackend

::: jinpy_utils.logger.ConsoleBackend
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - __init__
        - handle
        - _format_colored_message
        - _get_color_for_level

## File Backend

### FileBackend

::: jinpy_utils.logger.FileBackend
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - __init__
        - handle
        - _ensure_directory
        - _should_rotate
        - _rotate_file
        - shutdown

## REST API Backend

### RestApiBackend

::: jinpy_utils.logger.RestApiBackend
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - __init__
        - handle
        - _send_batch
        - _retry_request
        - _format_for_api
        - shutdown

## WebSocket Backend

### WebSocketBackend

::: jinpy_utils.logger.WebSocketBackend
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - __init__
        - handle
        - _connect
        - _reconnect
        - _send_message
        - _handle_disconnect
        - shutdown

## Backend Factory

### BackendFactory

::: jinpy_utils.logger.BackendFactory
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - create_backend
        - register_backend_type
        - get_registered_types

## Examples

### Console Backend Usage

```python
from jinpy_utils.logger import get_logger, LoggerConfig, ConsoleBackendConfig, LogLevel

config = LoggerConfig(
    backends=[
        ConsoleBackendConfig(
            level=LogLevel.DEBUG,
            use_colors=True,
            show_source=True,
            timestamp_format="%H:%M:%S.%f"
        )
    ]
)

logger = get_logger("console_app", config)
logger.info("This will be colored and formatted nicely")
```

### File Backend with Rotation

```python
from jinpy_utils.logger import get_logger, LoggerConfig, FileBackendConfig, LogLevel

config = LoggerConfig(
    backends=[
        FileBackendConfig(
            level=LogLevel.INFO,
            file_path="logs/app-{date}.log",
            max_size_mb=100,
            backup_count=10,
            compression=True,
            encoding="utf-8"
        )
    ]
)

logger = get_logger("file_app", config)
logger.info("This will be written to a rotating log file")
```

### REST API Backend

```python
from jinpy_utils.logger import get_logger, LoggerConfig, RestApiBackendConfig, LogLevel
import os

config = LoggerConfig(
    backends=[
        RestApiBackendConfig(
            level=LogLevel.ERROR,
            endpoint="https://logs.example.com/api/v1/logs",
            headers={
                "Authorization": f"Bearer {os.environ['LOG_API_TOKEN']}",
                "Content-Type": "application/json"
            },
            timeout_seconds=30,
            retry_count=3,
            batch_size=50,
            batch_timeout=10.0
        )
    ]
)

logger = get_logger("api_app", config)
logger.error("This error will be sent to the REST API")
```

### WebSocket Backend

```python
from jinpy_utils.logger import get_logger, LoggerConfig, WebSocketBackendConfig, LogLevel

config = LoggerConfig(
    backends=[
        WebSocketBackendConfig(
            level=LogLevel.INFO,
            endpoint="wss://logs.example.com/ws",
            headers={
                "Authorization": "Bearer YOUR_TOKEN"
            },
            reconnect_interval=5.0,
            max_reconnect_attempts=10
        )
    ]
)

logger = get_logger("websocket_app", config)
logger.info("This will be sent via WebSocket")
```

### Multiple Backends

```python
from jinpy_utils.logger import (
    get_logger, LoggerConfig,
    ConsoleBackendConfig, FileBackendConfig, RestApiBackendConfig,
    LogLevel
)

config = LoggerConfig(
    backends=[
        # Console for development
        ConsoleBackendConfig(
            level=LogLevel.DEBUG,
            use_colors=True
        ),
        # File for persistence
        FileBackendConfig(
            level=LogLevel.INFO,
            file_path="logs/app.log",
            max_size_mb=50,
            backup_count=5
        ),
        # REST API for centralized logging
        RestApiBackendConfig(
            level=LogLevel.ERROR,
            endpoint="https://logs.company.com/api/logs",
            batch_size=10
        )
    ]
)

logger = get_logger("multi_backend_app", config)

# DEBUG: only to console
logger.debug("Debug information")

# INFO: to console and file
logger.info("Application started")

# ERROR: to all backends
logger.error("Critical error occurred")
```

### Custom Backend

```python
from jinpy_utils.logger import BaseBackend, LogEntry, BackendFactory
from typing import Any

class CustomBackend(BaseBackend):
    """Custom backend implementation."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.custom_config = kwargs

    def handle(self, entry: LogEntry) -> None:
        """Handle a log entry."""
        if self.should_handle(entry):
            formatted = self.format_entry(entry)
            # Your custom logic here
            self._send_to_custom_destination(formatted)

    def _send_to_custom_destination(self, message: str) -> None:
        """Send message to custom destination."""
        # Implement your custom sending logic
        pass

    def shutdown(self) -> None:
        """Clean up resources."""
        # Implement cleanup logic
        pass

# Register the custom backend
BackendFactory.register_backend_type("custom", CustomBackend)

# Use the custom backend
from jinpy_utils.logger import get_logger, LoggerConfig

config = LoggerConfig(
    backends=[
        {
            "type": "custom",
            "level": "INFO",
            # Custom configuration parameters
            "custom_param": "value"
        }
    ]
)

logger = get_logger("custom_app", config)
```

### Async Backend Operations

```python
import asyncio
from jinpy_utils.logger import get_logger, create_production_config

async def async_logging_example():
    """Example of async logging operations."""
    config = create_production_config()
    logger = get_logger("async_app", config)

    # These operations are non-blocking when async is enabled
    logger.info("Starting async operation")
    await asyncio.sleep(0.1)
    logger.info("Async operation completed")

    # Ensure all logs are flushed before exit
    await logger.shutdown()

asyncio.run(async_logging_example())
```

## Backend Configuration

### Performance Tuning

```python
from jinpy_utils.logger import LoggerConfig, FileBackendConfig

# High-performance file backend
high_perf_config = LoggerConfig(
    backends=[
        FileBackendConfig(
            file_path="logs/high-perf.log",
            buffer_size=65536,      # 64KB buffer
            flush_interval=5.0,     # Flush every 5 seconds
            async_enabled=True,     # Enable async I/O
            compression=False       # Disable compression for speed
        )
    ]
)
```

### Error Handling

```python
from jinpy_utils.logger import LoggerConfig, RestApiBackendConfig

# Robust REST API backend
robust_config = LoggerConfig(
    backends=[
        RestApiBackendConfig(
            endpoint="https://logs.example.com/api/logs",
            timeout_seconds=30,
            retry_count=5,
            retry_backoff_factor=2.0,  # Exponential backoff
            max_queue_size=10000,      # Large queue for resilience
            fallback_to_file=True,     # Fallback to file on failure
            fallback_file="logs/api_fallback.log"
        )
    ]
)
```

### Security Configuration

```python
from jinpy_utils.logger import LoggerConfig, RestApiBackendConfig

# Secure API backend
secure_config = LoggerConfig(
    backends=[
        RestApiBackendConfig(
            endpoint="https://logs.example.com/api/logs",
            headers={
                "Authorization": "Bearer YOUR_TOKEN",
                "X-API-Key": "YOUR_API_KEY"
            },
            verify_ssl=True,           # Verify SSL certificates
            client_cert="client.pem",  # Client certificate
            client_key="client.key",   # Client private key
            encrypt_payload=True,      # Encrypt log payloads
            encryption_key="your_key"  # Encryption key
        )
    ]
)
```

## Backend Lifecycle

### Initialization

```python
from jinpy_utils.logger import BackendFactory, ConsoleBackendConfig

# Backends are created by the factory
backend_config = ConsoleBackendConfig(level="INFO")
backend = BackendFactory.create_backend(backend_config)
```

### Resource Management

```python
from jinpy_utils.logger import get_logger, create_production_config

# Proper resource cleanup
config = create_production_config()
logger = get_logger("app", config)

try:
    # Use logger
    logger.info("Application running")
finally:
    # Ensure proper shutdown
    logger.shutdown()
```

### Health Monitoring

```python
from jinpy_utils.logger import get_logger

logger = get_logger("app")

# Check backend health
for backend in logger.get_backends():
    if hasattr(backend, 'is_healthy'):
        health_status = backend.is_healthy()
        logger.info("Backend health",
                   backend_type=type(backend).__name__,
                   healthy=health_status)
```
