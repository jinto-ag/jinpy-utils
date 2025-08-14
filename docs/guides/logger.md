# Logger Guide

This guide shows you how to use the jinpy-utils logger effectively.

## Quick Start

```python
from jinpy_utils.logger import get_logger

# Create a logger
logger = get_logger("my_app")

# Log messages with structured data
logger.info("User logged in", user_id=123, action="login")
logger.warning("High memory usage", usage_percent=85)
logger.error("Database connection failed", error="Connection timeout")
```

## Configuration

```python
from jinpy_utils.logger import get_logger, create_production_config, set_global_config

# Set global production configuration
set_global_config(create_production_config())
logger = get_logger("production_app")

# Or use default configuration
logger = get_logger("my_app")  # Uses default configuration
```

For detailed configuration options, see the [Configuration API reference](../reference/logger/config.md).

## Backends

The logger supports multiple output backends:

- **Console**: For development and debugging
- **File**: For persistent logging with rotation
- **REST API**: For centralized logging services
- **WebSocket**: For real-time log streaming

For complete backend documentation, see the [Backends API reference](../reference/logger/backends.md).

## Error Handling

```python
from jinpy_utils.logger import get_logger
from jinpy_utils.logger import JPYLoggerError

logger = get_logger("error_example")

try:
    # Your application code
    pass
except JPYLoggerError as e:
    print(f"Logger error: {e.message}")
```

## Best Practices

1. **Use structured logging**: Include relevant context as keyword arguments
2. **Choose appropriate levels**: DEBUG for development, INFO for production events
3. **Handle errors gracefully**: Catch and handle logger-specific exceptions
4. **Configure for environment**: Use different configs for dev/prod

## Complete API Reference

For complete API documentation, see:

- [Core Logger API](../reference/logger/core.md)
- [Configuration API](../reference/logger/config.md)
- [Backends API](../reference/logger/backends.md)
- [Exceptions API](../reference/logger/exceptions.md)
