# Logger Exceptions API

Exception classes specific to the logger module.

## Base Logger Exception

### JPYLoggerError

::: jinpy_utils.logger.JPYLoggerError
    options:
      show_source: true
      show_signature_annotations: true

## Specific Logger Exceptions

### JPYLoggerBackendError

::: jinpy_utils.logger.JPYLoggerBackendError
    options:
      show_source: true
      show_signature_annotations: true

### JPYLoggerConfigurationError

::: jinpy_utils.logger.JPYLoggerConfigurationError
    options:
      show_source: true
      show_signature_annotations: true

### JPYLoggerConnectionError

::: jinpy_utils.logger.JPYLoggerConnectionError
    options:
      show_source: true
      show_signature_annotations: true

### JPYLoggerPerformanceError

::: jinpy_utils.logger.JPYLoggerPerformanceError
    options:
      show_source: true
      show_signature_annotations: true

### JPYLoggerSecurityError

::: jinpy_utils.logger.JPYLoggerSecurityError
    options:
      show_source: true
      show_signature_annotations: true

### JPYLoggerWebSocketError

::: jinpy_utils.logger.JPYLoggerWebSocketError
    options:
      show_source: true
      show_signature_annotations: true

## Usage Examples

### Configuration Errors

```python
from jinpy_utils.logger import LoggerConfig, ConsoleBackendConfig
from jinpy_utils.logger import JPYLoggerConfigurationError

try:
    config = LoggerConfig(
        level="INVALID_LEVEL",  # Invalid level
        backends=[ConsoleBackendConfig()]
    )
    config.validate()
except JPYLoggerConfigurationError as e:
    print(f"Configuration error: {e.message}")
    print(f"Config key: {e.config_key}")
    print(f"Suggestions: {e.suggestions}")
```

### Backend Errors

```python
from jinpy_utils.logger import get_logger, LoggerConfig, FileBackendConfig
from jinpy_utils.logger import JPYLoggerBackendError

try:
    config = LoggerConfig(
        backends=[
            FileBackendConfig(
                file_path="/invalid/path/app.log"  # Invalid path
            )
        ]
    )
    logger = get_logger("app", config)
    logger.info("This will fail")
except JPYLoggerBackendError as e:
    print(f"Backend error: {e.message}")
    print(f"Backend type: {e.backend_type}")
    print(f"Operation: {e.operation}")
    print(f"Suggestions: {e.suggestions}")
```

### Connection Errors

```python
from jinpy_utils.logger import get_logger, LoggerConfig, RestApiBackendConfig
from jinpy_utils.logger import JPYLoggerConnectionError

try:
    config = LoggerConfig(
        backends=[
            RestApiBackendConfig(
                endpoint="https://invalid-domain.com/logs"
            )
        ]
    )
    logger = get_logger("app", config)
    logger.error("This will fail to send")
except JPYLoggerConnectionError as e:
    print(f"Connection error: {e.message}")
    print(f"Endpoint: {e.endpoint}")
    print(f"Status code: {e.status_code}")
    print(f"Retry count: {e.retry_count}")
```

### WebSocket Errors

```python
from jinpy_utils.logger import get_logger, LoggerConfig, WebSocketBackendConfig
from jinpy_utils.logger import JPYLoggerWebSocketError

try:
    config = LoggerConfig(
        backends=[
            WebSocketBackendConfig(
                endpoint="wss://invalid-ws.com/logs"
            )
        ]
    )
    logger = get_logger("app", config)
    logger.info("This will fail WebSocket connection")
except JPYLoggerWebSocketError as e:
    print(f"WebSocket error: {e.message}")
    print(f"Endpoint: {e.endpoint}")
    print(f"Connection state: {e.connection_state}")
    print(f"Reconnect attempts: {e.reconnect_attempts}")
```

### Performance Errors

```python
from jinpy_utils.logger import get_logger, create_production_config
from jinpy_utils.logger import JPYLoggerPerformanceError
import time

try:
    logger = get_logger("perf_app", create_production_config())

    # Simulate performance issue
    for i in range(100000):
        logger.info(f"Message {i}")

except JPYLoggerPerformanceError as e:
    print(f"Performance error: {e.message}")
    print(f"Operation: {e.operation}")
    print(f"Duration: {e.duration_seconds}s")
    print(f"Threshold: {e.threshold_seconds}s")
```

### Security Errors

```python
from jinpy_utils.logger import get_logger, LoggerConfig, RestApiBackendConfig
from jinpy_utils.logger import JPYLoggerSecurityError

try:
    config = LoggerConfig(
        backends=[
            RestApiBackendConfig(
                endpoint="http://insecure-endpoint.com/logs",  # HTTP instead of HTTPS
                verify_ssl=True
            )
        ]
    )
    logger = get_logger("secure_app", config)
    logger.info("Sensitive information", credit_card="1234-5678-9012-3456")

except JPYLoggerSecurityError as e:
    print(f"Security error: {e.message}")
    print(f"Security violation: {e.violation_type}")
    print(f"Severity: {e.severity}")
    print(f"Suggestions: {e.suggestions}")
```

## Error Handling Patterns

### Comprehensive Error Handling

```python
from jinpy_utils.logger import get_logger, create_production_config
from jinpy_utils.logger import (
    JPYLoggerError,
    JPYLoggerBackendError,
    JPYLoggerConnectionError,
    JPYLoggerConfigurationError
)
from jinpy_utils.base import JPYBaseException

def setup_logger_with_error_handling(name: str):
    """Set up logger with comprehensive error handling."""
    try:
        config = create_production_config()
        logger = get_logger(name, config)
        return logger

    except JPYLoggerConfigurationError as e:
        print(f"Configuration error: {e.message}")
        # Fall back to basic console logging
        return get_logger(name)

    except JPYLoggerBackendError as e:
        print(f"Backend error: {e.message}")
        # Fall back to console-only logging
        fallback_config = create_development_config()
        return get_logger(name, fallback_config)

    except JPYLoggerError as e:
        print(f"General logger error: {e.message}")
        # Use Python's built-in logging as last resort
        import logging
        return logging.getLogger(name)

    except Exception as e:
        print(f"Unexpected error: {e}")
        import logging
        return logging.getLogger(name)
```

### Retry Logic for Connection Errors

```python
import time
from typing import Optional
from jinpy_utils.logger import get_logger, LoggerConfig
from jinpy_utils.logger import JPYLoggerConnectionError

def create_logger_with_retry(config: LoggerConfig, max_retries: int = 3) -> Optional:
    """Create logger with retry logic for connection errors."""
    for attempt in range(max_retries):
        try:
            logger = get_logger("retry_app", config)
            # Test the connection
            logger.info("Logger initialized successfully")
            return logger

        except JPYLoggerConnectionError as e:
            print(f"Attempt {attempt + 1} failed: {e.message}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries exceeded, using fallback logger")
                return get_logger("retry_app")  # Fallback to default config

    return None
```

### Graceful Degradation

```python
from jinpy_utils.logger import (
    get_logger,
    LoggerConfig,
    ConsoleBackendConfig,
    FileBackendConfig,
    RestApiBackendConfig
)
from jinpy_utils.logger import JPYLoggerBackendError

def create_resilient_logger(name: str) -> Logger:
    """Create logger with graceful degradation."""
    # Start with full configuration
    backends = [
        RestApiBackendConfig(endpoint="https://logs.example.com/api"),
        FileBackendConfig(file_path="logs/app.log"),
        ConsoleBackendConfig()
    ]

    # Try to remove backends that fail
    working_backends = []
    for backend_config in backends:
        try:
            test_config = LoggerConfig(backends=[backend_config])
            test_logger = get_logger(f"{name}_test", test_config)
            test_logger.info("Backend test")
            working_backends.append(backend_config)
        except JPYLoggerBackendError as e:
            print(f"Backend {type(backend_config).__name__} failed: {e.message}")
            continue

    # Use working backends
    if working_backends:
        config = LoggerConfig(backends=working_backends)
        return get_logger(name, config)
    else:
        # Last resort: basic Python logging
        import logging
        return logging.getLogger(name)
```

### Error Reporting

```python
from jinpy_utils.logger import get_logger
from jinpy_utils.logger import JPYLoggerError
from jinpy_utils.base import JPYBaseException

class LoggerErrorReporter:
    """Report logger errors to monitoring system."""

    def __init__(self):
        self.error_logger = get_logger("logger_errors")

    def report_error(self, error: JPYLoggerError, context: dict = None):
        """Report a logger error."""
        error_data = {
            "error_type": type(error).__name__,
            "error_code": error.error_code,
            "message": error.message,
            "context": context or {}
        }

        # Add specific error details
        if hasattr(error, 'backend_type'):
            error_data["backend_type"] = error.backend_type
        if hasattr(error, 'endpoint'):
            error_data["endpoint"] = error.endpoint
        if hasattr(error, 'config_key'):
            error_data["config_key"] = error.config_key

        self.error_logger.error("Logger error occurred", **error_data)

        # Send to monitoring system
        self._send_to_monitoring(error_data)

    def _send_to_monitoring(self, error_data: dict):
        """Send error data to monitoring system."""
        # Implementation depends on your monitoring system
        pass

# Usage
error_reporter = LoggerErrorReporter()

try:
    # Logger operations
    pass
except JPYLoggerError as e:
    error_reporter.report_error(e, {"operation": "logger_setup"})
```

## Custom Error Handling

### Custom Logger Exception

```python
from jinpy_utils.logger import JPYLoggerError

class CustomLoggerError(JPYLoggerError):
    """Custom logger exception for application-specific errors."""

    def __init__(self, message: str, custom_field: str = None, **kwargs):
        super().__init__(
            error_code="CUSTOM_LOGGER_ERROR",
            message=message,
            custom_field=custom_field,
            **kwargs
        )
```

### Error Context Management

```python
from contextlib import contextmanager
from jinpy_utils.logger import get_logger
from jinpy_utils.logger import JPYLoggerError

@contextmanager
def logger_error_context(operation: str, logger_name: str = "app"):
    """Context manager for logger error handling."""
    logger = get_logger("error_handler")
    logger.info(f"Starting {operation}")

    try:
        yield
        logger.info(f"Completed {operation}")
    except JPYLoggerError as e:
        logger.error(f"Logger error in {operation}",
                    error_code=e.error_code,
                    error_message=e.message)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in {operation}", error=str(e))
        raise

# Usage
with logger_error_context("log_setup"):
    # Logger setup code that might fail
    pass
```
