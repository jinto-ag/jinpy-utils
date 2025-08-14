# Logger Core API

Core logging classes and factory functions with synchronous and asynchronous
APIs, context binding, correlation IDs, and multiple pluggable backends.

## Factory Functions

### get_logger

::: jinpy_utils.logger.get_logger
    options:
      show_source: true
      show_signature_annotations: true

### set_global_config

::: jinpy_utils.logger.set_global_config
    options:
      show_source: true
      show_signature_annotations: true

### configure_from_env

::: jinpy_utils.logger.configure_from_env
    options:
      show_source: true
      show_signature_annotations: true

### shutdown_all_loggers

::: jinpy_utils.logger.shutdown_all_loggers
    options:
      show_source: true
      show_signature_annotations: true

## Core Classes

### Logger

::: jinpy_utils.logger.Logger
    options:
      show_root_heading: true
      show_root_toc_entry: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      members:
        - __init__
        - debug
        - info
        - warning
        - error
        - critical
        - log
        - adebug
        - ainfo
        - awarning
        - aerror
        - acritical
        - set_level
        - get_level
        - is_enabled_for
        - get_stats
        - get_backend_stats
        - bind
        - context
        - acontext
        - flush
        - close

### LoggerManager

::: jinpy_utils.logger.LoggerManager
    options:
      show_root_heading: true
      show_root_toc_entry: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      members:
        - get_logger
        - set_global_config
        - shutdown_all
        - get_all_loggers

## Data Models

### LogEntry

::: jinpy_utils.logger.backends.LogEntry
    options:
      show_source: true
      show_signature_annotations: true
      show_bases: true
      members:
        - __init__
        - to_dict
        - to_json

## Examples

### Basic Usage

```python
from jinpy_utils.logger import get_logger

# Get a logger instance
logger = get_logger("my_app")

# Log messages with structured data
logger.info("User logged in", user_id=123, ip="192.168.1.1")
logger.warning("High memory usage", usage_percent=85.2, threshold=80)
logger.error("Database error", error_code="DB001", retry_count=3)
```

### Advanced Configuration

```python
from jinpy_utils.logger import get_logger, LoggerConfig, ConsoleBackendConfig, LogLevel

# Custom configuration
config = LoggerConfig(
    level=LogLevel.DEBUG,
    backends=[
        ConsoleBackendConfig(
            level=LogLevel.DEBUG,
            use_colors=True,
            show_source=True
        )
    ]
)

logger = get_logger("advanced_app", config)
```

### Async Usage

```python
import asyncio
from jinpy_utils.logger import get_logger

async def async_operation():
    logger = get_logger("async_app")

    logger.info("Starting async operation")
    await asyncio.sleep(1)
    logger.info("Async operation completed")

# The logger automatically handles async contexts
asyncio.run(async_operation())
```

### Context Management

```python
from jinpy_utils.logger import get_logger
from contextlib import contextmanager

@contextmanager
def log_operation(operation_name: str):
    logger = get_logger("operations")
    logger.info(f"Starting {operation_name}")
    try:
        yield
        logger.info(f"Completed {operation_name}")
    except Exception as e:
        logger.error(f"Failed {operation_name}", error=str(e))
        raise

# Usage
with log_operation("user_registration"):
    # Your operation here
    pass
```

### Global Configuration

```python
from jinpy_utils.logger import set_global_config, get_logger, create_production_config

# Set global configuration
set_global_config(create_production_config())

# All subsequent loggers will use the global config
logger1 = get_logger("app1")
logger2 = get_logger("app2")
```

### Environment-Based Setup

```python
import os
from jinpy_utils.logger import configure_from_env, get_logger

# Set environment variables
os.environ['JINPY_LOG_LEVEL'] = 'DEBUG'
os.environ['JINPY_LOG_FORMAT'] = 'json'

# Configure from environment
config = configure_from_env()
logger = get_logger("env_app", config)
```

### Cleanup

```python
from jinpy_utils.logger import shutdown_all_loggers

# At application shutdown
shutdown_all_loggers()
```

## Performance Considerations

### Lazy Evaluation

The logger uses lazy evaluation for message formatting:

```python
# Efficient - formatting only happens if DEBUG is enabled
logger.debug("Processing item %d of %d", current_item, total_items)

# Less efficient - formatting happens regardless
logger.debug(f"Processing item {current_item} of {total_items}")
```

### Structured Logging Performance

```python
# Use keyword arguments for structured fields
logger.info("User action", user_id=123, action="login")  # Fast

# Avoid complex objects as values
logger.info("User action", user=user_object)  # Slower (serialization)
```

### Async Performance

```python
# For high-throughput applications, enable async mode
config = LoggerConfig(async_enabled=True, buffer_size=10000)
logger = get_logger("high_perf", config)
```

## Thread Safety

All logger operations are thread-safe:

```python
import threading
from jinpy_utils.logger import get_logger

logger = get_logger("threaded_app")

def worker(worker_id: int):
    logger.info("Worker started", worker_id=worker_id)
    # Safe to use from multiple threads

# Start multiple threads
threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

## Additional Use Cases

### HTTP microservice with request-scoped context

```python
from contextlib import asynccontextmanager
from jinpy_utils.logger import get_logger

logger = get_logger("api")

@asynccontextmanager
async def request_context(request_id: str, user_id: str | None):
    async with logger.acontext(request_id=request_id, user_id=user_id):
        yield

async def handle_request(req):
    async with request_context(req.id, req.user_id):
        await logger.ainfo("request_received", {"path": req.path})
        # ... application logic ...
        await logger.ainfo("request_completed")
```

### Background worker with batching backends

```python
import asyncio
from jinpy_utils.logger import get_logger

logger = get_logger("worker")

async def worker_loop():
    while True:
        await logger.ainfo("heartbeat")
        await asyncio.sleep(5)

asyncio.run(worker_loop())
```

### Multi-tenant applications with bound context

```python
from jinpy_utils.logger import get_logger

logger = get_logger("multi_tenant")
tenant_logger = logger.bind(tenant_id="t-1234")

tenant_logger.info("tenant_initialized")
```
