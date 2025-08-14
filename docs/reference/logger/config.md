# Logger Configuration API

Configuration classes, presets, and utilities for the logger module.

## Main Configuration

### LoggerConfig

::: jinpy_utils.logger.LoggerConfig
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - __init__
        - validate
        - to_dict
        - from_dict
        - add_backend
        - remove_backend
        - get_backend
        - merge

### GlobalLoggerConfig

::: jinpy_utils.logger.GlobalLoggerConfig
    options:
      show_source: true
      show_signature_annotations: true

## Backend Configurations

### BackendConfig

::: jinpy_utils.logger.BackendConfig
    options:
      show_source: true
      show_signature_annotations: true

### ConsoleBackendConfig

::: jinpy_utils.logger.ConsoleBackendConfig
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - level
        - format
        - use_colors
        - show_source
        - show_extra
        - timestamp_format
        - max_line_length

### FileBackendConfig

::: jinpy_utils.logger.FileBackendConfig
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - level
        - file_path
        - format
        - max_size_mb
        - backup_count
        - encoding
        - compression
        - create_dirs
        - file_mode
        - buffer_size
        - flush_interval

### RestApiBackendConfig

::: jinpy_utils.logger.RestApiBackendConfig
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - level
        - endpoint
        - headers
        - timeout_seconds
        - retry_count
        - retry_backoff_factor
        - batch_size
        - batch_timeout
        - max_queue_size
        - verify_ssl
        - client_cert
        - client_key

### WebSocketBackendConfig

::: jinpy_utils.logger.WebSocketBackendConfig
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - level
        - endpoint
        - headers
        - reconnect_interval
        - max_reconnect_attempts
        - ping_interval
        - ping_timeout
        - compression

### DatabaseBackendConfig

::: jinpy_utils.logger.DatabaseBackendConfig
    options:
      show_source: true
      show_signature_annotations: true

### RetryConfig

::: jinpy_utils.logger.RetryConfig
    options:
      show_source: true
      show_signature_annotations: true

### SecurityConfig

::: jinpy_utils.logger.SecurityConfig
    options:
      show_source: true
      show_signature_annotations: true

## Configuration Presets

### create_development_config

::: jinpy_utils.logger.create_development_config
    options:
      show_source: true
      show_signature_annotations: true

### create_production_config

::: jinpy_utils.logger.create_production_config
    options:
      show_source: true
      show_signature_annotations: true

### create_cloud_config

::: jinpy_utils.logger.create_cloud_config
    options:
      show_source: true
      show_signature_annotations: true

## Enums and Constants

### LogLevel

::: jinpy_utils.logger.LogLevel
    options:
      show_source: true
      show_signature_annotations: true

### LogFormat

::: jinpy_utils.logger.LogFormat
    options:
      show_source: true
      show_signature_annotations: true

### BackendType

::: jinpy_utils.logger.BackendType
    options:
      show_source: true
      show_signature_annotations: true

### BatchStrategy

::: jinpy_utils.logger.BatchStrategy
    options:
      show_source: true
      show_signature_annotations: true

### CompressionType

::: jinpy_utils.logger.CompressionType
    options:
      show_source: true
      show_signature_annotations: true

### ConnectionState

::: jinpy_utils.logger.ConnectionState
    options:
      show_source: true
      show_signature_annotations: true

### RetryStrategy

::: jinpy_utils.logger.RetryStrategy
    options:
      show_source: true
      show_signature_annotations: true

### SecurityLevel

::: jinpy_utils.logger.SecurityLevel
    options:
      show_source: true
      show_signature_annotations: true

## Examples

### Basic Configuration

```python
from jinpy_utils.logger import LoggerConfig, ConsoleBackendConfig, LogLevel

config = LoggerConfig(
    level=LogLevel.INFO,
    backends=[
        ConsoleBackendConfig(
            level=LogLevel.DEBUG,
            use_colors=True
        )
    ]
)
```

### File Logging Configuration

```python
from jinpy_utils.logger import LoggerConfig, FileBackendConfig, LogLevel, LogFormat

config = LoggerConfig(
    level=LogLevel.DEBUG,
    backends=[
        FileBackendConfig(
            level=LogLevel.INFO,
            file_path="logs/app.log",
            format=LogFormat.JSON,
            max_size_mb=50,
            backup_count=10,
            compression=True
        )
    ]
)
```

### Multiple Backend Configuration

```python
from jinpy_utils.logger import (
    LoggerConfig,
    ConsoleBackendConfig,
    FileBackendConfig,
    RestApiBackendConfig,
    LogLevel
)

config = LoggerConfig(
    level=LogLevel.DEBUG,
    async_enabled=True,
    backends=[
        ConsoleBackendConfig(
            level=LogLevel.DEBUG,
            use_colors=True
        ),
        FileBackendConfig(
            level=LogLevel.INFO,
            file_path="logs/app.log",
            max_size_mb=100,
            backup_count=5
        ),
        RestApiBackendConfig(
            level=LogLevel.ERROR,
            endpoint="https://logs.example.com/api/logs",
            batch_size=50
        )
    ]
)
```

### Environment-Based Configuration

```python
import os
from jinpy_utils.logger import LoggerConfig, create_development_config, create_production_config

def get_config() -> LoggerConfig:
    """Get configuration based on environment."""
    env = os.environ.get("ENVIRONMENT", "development")

    if env == "production":
        return create_production_config()
    elif env == "staging":
        return create_production_config(level=LogLevel.DEBUG)
    else:
        return create_development_config()

config = get_config()
```

### Configuration Validation

```python
from jinpy_utils.logger import LoggerConfig, ConsoleBackendConfig
from jinpy_utils.base import JPYConfigurationError

try:
    config = LoggerConfig(
        level=LogLevel.INFO,
        backends=[
            ConsoleBackendConfig(
                level=LogLevel.DEBUG
            )
        ]
    )
    config.validate()
except JPYConfigurationError as e:
    print(f"Configuration error: {e.message}")
```

### Dynamic Configuration Updates

```python
from jinpy_utils.logger import get_logger, LoggerConfig, FileBackendConfig

logger = get_logger("app")

# Add a new backend at runtime
file_backend = FileBackendConfig(
    level=LogLevel.WARNING,
    file_path="warnings.log"
)

logger.add_backend(file_backend)
```

### Configuration Serialization

```python
from jinpy_utils.logger import LoggerConfig, ConsoleBackendConfig
import json

# Create configuration
config = LoggerConfig(
    level=LogLevel.INFO,
    backends=[ConsoleBackendConfig(level=LogLevel.DEBUG)]
)

# Serialize to dictionary
config_dict = config.to_dict()

# Save to JSON file
with open("logger_config.json", "w") as f:
    json.dump(config_dict, f, indent=2)

# Load from JSON file
with open("logger_config.json", "r") as f:
    loaded_dict = json.load(f)

# Recreate configuration
loaded_config = LoggerConfig.from_dict(loaded_dict)
```

### Advanced REST API Configuration

```python
from jinpy_utils.logger import LoggerConfig, RestApiBackendConfig, RetryConfig, SecurityConfig

config = LoggerConfig(
    backends=[
        RestApiBackendConfig(
            level=LogLevel.INFO,
            endpoint="https://logs.example.com/api/v1/logs",
            headers={
                "Authorization": "Bearer YOUR_TOKEN",
                "Content-Type": "application/json",
                "X-Source": "jinpy-utils"
            },
            timeout_seconds=30,
            retry_config=RetryConfig(
                max_attempts=5,
                backoff_factor=2.0,
                backoff_strategy=RetryStrategy.EXPONENTIAL
            ),
            security_config=SecurityConfig(
                encrypt_payload=True,
                verify_ssl=True,
                security_level=SecurityLevel.HIGH
            ),
            batch_size=100,
            batch_timeout=10.0,
            max_queue_size=10000
        )
    ]
)
```

### Cloud-Optimized Configuration

```python
from jinpy_utils.logger import create_cloud_config
import os

config = create_cloud_config(
    service_name=os.environ.get("SERVICE_NAME", "my-service"),
    environment=os.environ.get("ENVIRONMENT", "production"),
    version=os.environ.get("SERVICE_VERSION", "1.0.0"),
    cloud_provider=os.environ.get("CLOUD_PROVIDER", "aws"),  # aws, gcp, azure
    region=os.environ.get("AWS_REGION", "us-east-1")
)
```

### WebSocket Configuration with Reconnection

```python
from jinpy_utils.logger import LoggerConfig, WebSocketBackendConfig

config = LoggerConfig(
    backends=[
        WebSocketBackendConfig(
            level=LogLevel.INFO,
            endpoint="wss://logs.example.com/ws",
            headers={
                "Authorization": "Bearer YOUR_TOKEN"
            },
            reconnect_interval=5.0,
            max_reconnect_attempts=10,
            ping_interval=30.0,
            ping_timeout=10.0,
            compression=True
        )
    ]
)
```

## Configuration Best Practices

### Environment Variables

```python
import os
from jinpy_utils.logger import LoggerConfig, FileBackendConfig, LogLevel

def create_config_from_env() -> LoggerConfig:
    """Create configuration from environment variables."""
    return LoggerConfig(
        level=LogLevel[os.environ.get("LOG_LEVEL", "INFO")],
        async_enabled=os.environ.get("LOG_ASYNC", "true").lower() == "true",
        backends=[
            FileBackendConfig(
                file_path=os.environ.get("LOG_FILE", "app.log"),
                max_size_mb=int(os.environ.get("LOG_MAX_SIZE_MB", "100")),
                backup_count=int(os.environ.get("LOG_BACKUP_COUNT", "5"))
            )
        ]
    )
```

### Configuration Hierarchy

```python
from pathlib import Path
import yaml
from jinpy_utils.logger import LoggerConfig

def load_hierarchical_config() -> LoggerConfig:
    """Load configuration with hierarchy."""
    config_sources = [
        Path("/etc/myapp/logging.yaml"),        # System config
        Path.home() / ".myapp" / "logging.yaml", # User config
        Path("logging.yaml"),                    # Local config
    ]

    merged_config = {}
    for config_file in config_sources:
        if config_file.exists():
            with open(config_file) as f:
                config = yaml.safe_load(f)
                merged_config.update(config)

    return LoggerConfig.from_dict(merged_config.get("logger", {}))
```

### Configuration Validation

```python
from jinpy_utils.logger import LoggerConfig
from jinpy_utils.base import JPYConfigurationError

def validate_production_config(config: LoggerConfig) -> None:
    """Validate configuration for production use."""
    if config.level.value < LogLevel.INFO.value:
        raise JPYConfigurationError(
            message="Production logging level should be INFO or higher",
            config_key="level",
            suggestions=["Set level to INFO, WARNING, or ERROR"]
        )

    if not config.async_enabled:
        raise JPYConfigurationError(
            message="Async logging should be enabled in production",
            config_key="async_enabled",
            suggestions=["Set async_enabled to True for better performance"]
        )
```

### Testing Configuration

```python
from jinpy_utils.logger import LoggerConfig, ConsoleBackendConfig, LogLevel

def create_test_config() -> LoggerConfig:
    """Create configuration optimized for testing."""
    return LoggerConfig(
        level=LogLevel.WARNING,  # Reduce noise in tests
        async_enabled=False,     # Synchronous for predictable testing
        backends=[
            ConsoleBackendConfig(
                level=LogLevel.WARNING,
                use_colors=False,    # No colors in test output
                show_source=False    # Cleaner test output
            )
        ]
    )
```
