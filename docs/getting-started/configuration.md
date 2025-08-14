# Configuration

This guide covers all configuration options for jinpy-utils, from basic setup to advanced production configurations.

## Overview

jinpy-utils uses a layered configuration approach:

1. **Default Configuration** - Built-in defaults for quick start
2. **Environment Variables** - Override defaults with environment variables
3. **Configuration Files** - YAML, JSON, or Python files for complex setups
4. **Programmatic Configuration** - Direct configuration in code

## Logger Configuration

The logger is the most configurable component in jinpy-utils. Here's how to set it up for different scenarios.

### Quick Setup

For most use cases, use the built-in configuration presets:

```python
from jinpy_utils.logger import get_logger, create_development_config, create_production_config

# Development: human-readable, all levels, console output
dev_logger = get_logger("app", create_development_config())

# Production: JSON format, INFO+, optimized performance
prod_logger = get_logger("app", create_production_config())
```

### Environment-Based Configuration

Configure loggers using environment variables:

```python
from jinpy_utils.logger import get_logger, configure_from_env
import os

# Set environment variables
os.environ['JINPY_LOG_LEVEL'] = 'DEBUG'
os.environ['JINPY_LOG_FORMAT'] = 'json'
os.environ['JINPY_LOG_FILE'] = '/var/log/app.log'

# Configure from environment
config = configure_from_env()
logger = get_logger("app", config)
```

### Supported Environment Variables

| Variable | Description | Default | Values |
|----------|-------------|---------|---------|
| `JINPY_LOG_LEVEL` | Global log level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `JINPY_LOG_FORMAT` | Output format | `structured` | `json`, `structured`, `simple` |
| `JINPY_LOG_FILE` | Log file path | None | Any valid file path |
| `JINPY_LOG_MAX_SIZE` | File rotation size (MB) | `10` | Any positive integer |
| `JINPY_LOG_BACKUP_COUNT` | Number of backup files | `5` | Any positive integer |
| `JINPY_LOG_CONSOLE` | Enable console output | `true` | `true`, `false` |
| `JINPY_LOG_ASYNC` | Enable async logging | `true` | `true`, `false` |

### Custom Configuration

Create detailed configurations for specific needs:

```python
from jinpy_utils.logger import (
    get_logger,
    LoggerConfig,
    ConsoleBackendConfig,
    FileBackendConfig,
    LogLevel,
    LogFormat
)

# Custom configuration
config = LoggerConfig(
    level=LogLevel.DEBUG,
    async_enabled=True,
    backends=[
        # Console backend for development
        ConsoleBackendConfig(
            level=LogLevel.DEBUG,
            format=LogFormat.STRUCTURED,
            use_colors=True
        ),
        # File backend for persistence
        FileBackendConfig(
            level=LogLevel.INFO,
            file_path="logs/app.log",
            format=LogFormat.JSON,
            max_size_mb=50,
            backup_count=10,
            encoding="utf-8"
        )
    ]
)

logger = get_logger("custom_app", config)
```

## Configuration Files

For complex setups, use configuration files.

### YAML Configuration

Create a `logger_config.yaml` file:

```yaml title="logger_config.yaml"
# Logger Configuration
logger:
  level: INFO
  async_enabled: true

  # Global settings
  global:
    timezone: UTC
    date_format: "%Y-%m-%d %H:%M:%S"

  # Backend configurations
  backends:
    - type: console
      level: DEBUG
      format: structured
      use_colors: true

    - type: file
      level: INFO
      file_path: "logs/app.log"
      format: json
      max_size_mb: 100
      backup_count: 5
      encoding: utf-8

    - type: rest_api
      level: ERROR
      endpoint: "https://logs.example.com/api/v1/logs"
      headers:
        Authorization: "Bearer ${LOG_API_TOKEN}"
        Content-Type: "application/json"
      timeout_seconds: 30
      retry_count: 3
      batch_size: 100

# Application-specific settings
app:
  environment: production
  debug: false
  features:
    - structured_logging
    - error_tracking
```

Load the configuration:

```python
import yaml
from jinpy_utils.logger import get_logger, LoggerConfig

# Load YAML configuration
with open("logger_config.yaml", "r") as f:
    config_data = yaml.safe_load(f)

# Convert to LoggerConfig (you'll need to implement this conversion)
config = LoggerConfig.from_dict(config_data["logger"])
logger = get_logger("app", config)
```

### JSON Configuration

Create a `logger_config.json` file:

```json title="logger_config.json"
{
  "logger": {
    "level": "INFO",
    "async_enabled": true,
    "backends": [
      {
        "type": "console",
        "level": "DEBUG",
        "format": "structured",
        "use_colors": true
      },
      {
        "type": "file",
        "level": "INFO",
        "file_path": "logs/app.log",
        "format": "json",
        "max_size_mb": 100,
        "backup_count": 5
      }
    ]
  },
  "app": {
    "environment": "production",
    "debug": false
  }
}
```

## Environment-Specific Configurations

### Development Configuration

Optimized for development and debugging:

```python
from jinpy_utils.logger import LoggerConfig, ConsoleBackendConfig, LogLevel, LogFormat

dev_config = LoggerConfig(
    level=LogLevel.DEBUG,
    async_enabled=False,  # Synchronous for immediate output
    backends=[
        ConsoleBackendConfig(
            level=LogLevel.DEBUG,
            format=LogFormat.STRUCTURED,  # Human-readable
            use_colors=True,
            show_source=True,
            show_extra=True
        )
    ]
)
```

### Testing Configuration

Configuration for automated testing:

```python
from jinpy_utils.logger import LoggerConfig, ConsoleBackendConfig, LogLevel, LogFormat

test_config = LoggerConfig(
    level=LogLevel.WARNING,  # Reduce noise in tests
    async_enabled=False,     # Synchronous for predictable testing
    backends=[
        ConsoleBackendConfig(
            level=LogLevel.WARNING,
            format=LogFormat.SIMPLE,  # Minimal output
            use_colors=False
        )
    ]
)
```

### Production Configuration

High-performance configuration for production:

```python
from jinpy_utils.logger import (
    LoggerConfig,
    FileBackendConfig,
    RestApiBackendConfig,
    LogLevel,
    LogFormat
)

prod_config = LoggerConfig(
    level=LogLevel.INFO,
    async_enabled=True,  # High performance
    buffer_size=10000,   # Large buffer for performance
    flush_interval=5.0,  # Flush every 5 seconds
    backends=[
        # File logging for local debugging
        FileBackendConfig(
            level=LogLevel.INFO,
            file_path="/var/log/app/app.log",
            format=LogFormat.JSON,
            max_size_mb=500,
            backup_count=20,
            compression=True
        ),
        # Remote logging for centralized monitoring
        RestApiBackendConfig(
            level=LogLevel.ERROR,  # Only errors to remote
            endpoint="https://logs.company.com/api/v1/logs",
            timeout_seconds=30,
            retry_count=3,
            batch_size=500
        )
    ]
)
```

### Cloud Configuration

Configuration optimized for cloud environments:

```python
from jinpy_utils.logger import create_cloud_config
import os

# Automatically configures for cloud environments
# Detects: AWS CloudWatch, GCP Cloud Logging, Azure Monitor
cloud_config = create_cloud_config(
    service_name=os.environ.get("SERVICE_NAME", "my-service"),
    environment=os.environ.get("ENVIRONMENT", "production"),
    version=os.environ.get("SERVICE_VERSION", "1.0.0")
)
```

## Backend-Specific Configuration

### Console Backend

```python
from jinpy_utils.logger import ConsoleBackendConfig, LogLevel, LogFormat

console_config = ConsoleBackendConfig(
    level=LogLevel.DEBUG,
    format=LogFormat.STRUCTURED,
    use_colors=True,
    show_source=True,      # Show file:line information
    show_extra=True,       # Show extra fields
    timestamp_format="%H:%M:%S.%f",
    max_line_length=120    # Wrap long lines
)
```

### File Backend

```python
from jinpy_utils.logger import FileBackendConfig, LogLevel, LogFormat

file_config = FileBackendConfig(
    level=LogLevel.INFO,
    file_path="logs/app-{date}.log",  # Date-based rotation
    format=LogFormat.JSON,
    max_size_mb=100,
    backup_count=30,
    encoding="utf-8",
    compression=True,          # Compress rotated files
    create_dirs=True,         # Create log directory if needed
    file_mode="a",            # Append mode
    buffer_size=8192,         # File buffer size
    flush_interval=1.0        # Flush to disk every second
)
```

### REST API Backend

```python
from jinpy_utils.logger import RestApiBackendConfig, LogLevel

api_config = RestApiBackendConfig(
    level=LogLevel.ERROR,
    endpoint="https://logs.example.com/api/v1/logs",
    headers={
        "Authorization": "Bearer YOUR_API_TOKEN",
        "Content-Type": "application/json",
        "User-Agent": "jinpy-utils/1.0.0"
    },
    timeout_seconds=30,
    retry_count=3,
    retry_backoff_factor=2.0,  # Exponential backoff
    batch_size=100,            # Batch multiple logs
    batch_timeout=10.0,        # Send batch after 10 seconds
    max_queue_size=10000,      # Maximum queued logs
    include_metadata=True      # Include system metadata
)
```

### WebSocket Backend

```python
from jinpy_utils.logger import WebSocketBackendConfig, LogLevel

ws_config = WebSocketBackendConfig(
    level=LogLevel.INFO,
    endpoint="wss://logs.example.com/ws",
    headers={
        "Authorization": "Bearer YOUR_TOKEN"
    },
    reconnect_interval=5.0,    # Reconnect after 5 seconds
    max_reconnect_attempts=10,
    ping_interval=30.0,        # Ping every 30 seconds
    ping_timeout=10.0,
    compression=True
)
```

## Dynamic Configuration

Update configuration at runtime:

```python
from jinpy_utils.logger import get_logger, set_global_config

logger = get_logger("app")

# Change log level at runtime
logger.set_level(LogLevel.DEBUG)

# Add new backend at runtime
from jinpy_utils.logger import FileBackendConfig
file_backend = FileBackendConfig(
    level=LogLevel.WARNING,
    file_path="runtime.log"
)
logger.add_backend(file_backend)

# Update global configuration
new_config = create_production_config()
set_global_config(new_config)
```

## Configuration Validation

Validate configuration before use:

```python
from jinpy_utils.logger import LoggerConfig, ConfigurationError

try:
    config = LoggerConfig(
        level=LogLevel.INFO,
        backends=[]  # Empty backends list
    )
    config.validate()
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    # Handle configuration error
```

## Best Practices

### 1. Environment-Based Configuration

```python
import os
from jinpy_utils.logger import get_logger

def get_app_logger():
    env = os.environ.get("ENVIRONMENT", "development")

    if env == "production":
        config = create_production_config()
    elif env == "testing":
        config = create_test_config()
    else:
        config = create_development_config()

    return get_logger("app", config)
```

### 2. Configuration Hierarchy

```python
from pathlib import Path
import yaml

def load_config():
    """Load configuration with fallbacks."""
    config_paths = [
        Path("/etc/myapp/config.yaml"),      # System config
        Path.home() / ".myapp" / "config.yaml",  # User config
        Path("config.yaml"),                  # Local config
    ]

    config = {}
    for path in config_paths:
        if path.exists():
            with open(path) as f:
                config.update(yaml.safe_load(f))

    return config
```

### 3. Secrets Management

```python
import os
from jinpy_utils.logger import RestApiBackendConfig

# Don't hardcode secrets
api_config = RestApiBackendConfig(
    endpoint=os.environ["LOG_API_ENDPOINT"],
    headers={
        "Authorization": f"Bearer {os.environ['LOG_API_TOKEN']}"
    }
)
```

### 4. Configuration Documentation

Document your configuration schema:

```python
from typing import TypedDict, List, Optional

class LoggerConfigDict(TypedDict):
    """Logger configuration schema."""
    level: str
    async_enabled: bool
    backends: List[dict]

class AppConfigDict(TypedDict):
    """Application configuration schema."""
    logger: LoggerConfigDict
    database_url: str
    redis_url: Optional[str]
```

## Troubleshooting Configuration

### Common Issues

#### 1. Configuration Not Loading

**Problem**: Configuration changes not taking effect.

**Solution**: Ensure you're passing the config to `get_logger()`:

```python
# Wrong
logger = get_logger("app")
config = create_production_config()

# Correct
config = create_production_config()
logger = get_logger("app", config)
```

#### 2. File Permissions

**Problem**: Can't write to log file.

**Solution**: Check file permissions and directory existence:

```python
from pathlib import Path

log_path = Path("logs/app.log")
log_path.parent.mkdir(parents=True, exist_ok=True)
```

#### 3. Environment Variables Not Working

**Problem**: Environment variables being ignored.

**Solution**: Ensure variables are set before importing:

```bash
export JINPY_LOG_LEVEL=DEBUG
python your_app.py
```

### Debugging Configuration

Enable debug logging for configuration:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# jinpy-utils will now log configuration details
from jinpy_utils.logger import get_logger, create_production_config

logger = get_logger("app", create_production_config())
```

## Next Steps

- [Logger Guide](../guides/logger.md) - Deep dive into logging features
- [API Reference](../reference/logger/config.md) - Complete configuration API
