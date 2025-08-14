"""Configuration management for the logger module.

This module provides configuration classes that support both
environment-based and programmatic configuration following
12-factor app principles.
"""

import os
from pathlib import Path
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from jinpy_utils.logger.enums import (
    BackendType,
    BatchStrategy,
    CompressionType,
    LogFormat,
    LogLevel,
    RetryStrategy,
    SecurityLevel,
)
from jinpy_utils.logger.exceptions import JPYLoggerConfigurationError


class SecurityConfig(BaseModel):
    """Security configuration for logger backends."""

    level: SecurityLevel = SecurityLevel.NONE
    api_key: str | None = Field(default=None, description="API key for authentication")
    tls_cert_path: Path | None = Field(default=None, description="TLS certificate path")
    tls_key_path: Path | None = Field(default=None, description="TLS private key path")
    ca_cert_path: Path | None = Field(default=None, description="CA certificate path")
    verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates",
    )
    oauth2_token: str | None = Field(
        default=None,
        description="OAuth2 access token",
    )

    @field_validator("api_key", "oauth2_token")
    @classmethod
    def validate_secrets(cls, v: str | None) -> str | None:
        """Validate secret fields by checking environment variables."""
        if v and v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]
            return os.getenv(env_var)
        return v


class RetryConfig(BaseModel):
    """Retry configuration for backend operations."""

    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    max_attempts: int = Field(default=3, ge=1, le=10)
    base_delay: float = Field(default=1.0, gt=0)
    max_delay: float = Field(default=60.0, gt=0)
    backoff_multiplier: float = Field(default=2.0, gt=1)
    jitter: bool = Field(
        default=True,
        description="Add random jitter to delays",
    )


class BackendConfig(BaseModel):
    """Base configuration for logging backends."""

    backend_type: BackendType
    name: str = Field(..., description="Unique backend name")
    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.JSON
    enabled: bool = True
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)

    # Performance settings
    buffer_size: int = Field(
        default=1000,
        gt=0,
        description="Buffer size for batching",
    )
    flush_interval: float = Field(
        default=5.0, gt=0, description="Flush interval in seconds"
    )
    timeout: float = Field(
        default=30.0, gt=0, description="Operation timeout in seconds"
    )

    model_config = ConfigDict(extra="allow", use_enum_values=True)


class ConsoleBackendConfig(BackendConfig):
    """Configuration for console logging backend."""

    backend_type: BackendType = BackendType.CONSOLE
    format: LogFormat = LogFormat.CONSOLE
    colors: bool = Field(default=True, description="Enable colored output")
    stream: str = Field(default="stdout", pattern="^(stdout|stderr)$")


class FileBackendConfig(BackendConfig):
    """Configuration for file logging backend."""

    backend_type: BackendType = BackendType.FILE
    file_path: Path = Field(
        default=Path("logs/app.log"),
        description="Log file path",
    )
    max_size_mb: int | None = Field(
        default=100, gt=0, description="Max file size in MB"
    )
    backup_count: int = Field(
        default=5,
        ge=0,
        description="Number of backup files",
    )
    compression: CompressionType = CompressionType.GZIP
    encoding: str = Field(default="utf-8", description="File encoding")

    @field_validator("file_path")
    @classmethod
    def create_log_directory(cls, v: Path) -> Path:
        """Create log directory if it doesn't exist."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v


class RestApiBackendConfig(BackendConfig):
    """Configuration for REST API logging backend."""

    backend_type: BackendType = BackendType.REST_API
    base_url: str = Field(..., description="Base URL for the logging API")
    endpoint: str = Field(default="/logs", description="Logging endpoint path")
    method: str = Field(default="POST", pattern="^(POST|PUT|PATCH)$")
    headers: dict[str, str] = Field(
        default_factory=dict, description="Additional headers"
    )
    batch_strategy: BatchStrategy = BatchStrategy.HYBRID

    @field_validator("base_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise JPYLoggerConfigurationError(
                message="Invalid URL format - must start with http:// or https://",
                config_section="base_url",
                config_value=v,
            )
        return v.rstrip("/")


class WebSocketBackendConfig(BackendConfig):
    """Configuration for WebSocket logging backend."""

    backend_type: BackendType = BackendType.WEBSOCKET
    ws_url: str = Field(..., description="WebSocket URL")
    reconnect_interval: float = Field(
        default=5.0, gt=0, description="Reconnection interval"
    )
    ping_interval: float = Field(
        default=30.0,
        gt=0,
        description="Ping interval",
    )
    max_message_size: int = Field(
        default=1024 * 1024, gt=0, description="Max message size"
    )

    @field_validator("ws_url")
    @classmethod
    def validate_ws_url(cls, v: str) -> str:
        """Validate WebSocket URL format."""
        if not v.startswith(("ws://", "wss://")):
            raise JPYLoggerConfigurationError(
                message="Invalid WebSocket URL format - must start with ws:// or wss://",
                config_section="ws_url",
                config_value=v,
            )
        return v


class DatabaseBackendConfig(BackendConfig):
    """Configuration for database logging backend."""

    backend_type: BackendType = BackendType.DATABASE
    connection_string: str = Field(
        ...,
        description="Database connection string",
    )
    table_name: str = Field(default="logs", description="Table name for logs")
    schema_name: str | None = Field(default=None, description="Schema name")
    pool_size: int = Field(default=5, gt=0, description="Connection pool size")
    pool_timeout: float = Field(default=30.0, gt=0, description="Pool timeout")


class GlobalLoggerConfig(BaseModel):
    """Global logger configuration following 12-factor app principles."""

    # Basic settings
    app_name: str = Field(default="jinpy-utils", description="Application name")
    environment: str = Field(
        default="development",
        description="Environment name",
    )
    version: str = Field(default="1.0.0", description="Application version")

    # Default log settings
    default_level: LogLevel = LogLevel.INFO
    correlation_id_header: str = Field(default="X-Correlation-ID")
    enable_correlation_ids: bool = True
    enable_structured_context: bool = True

    # Performance settings
    max_context_size: int = Field(default=10000, gt=0)
    async_queue_size: int = Field(default=10000, gt=0)
    enable_performance_metrics: bool = False

    # Security settings
    enable_sanitization: bool = Field(
        default=True, description="Sanitize sensitive data"
    )
    sensitive_fields: list[str] = Field(
        default_factory=lambda: ["password", "token", "secret", "key", "auth"],
        description="Fields to sanitize in logs",
    )

    # Backends configuration
    backends: list[
        ConsoleBackendConfig
        | FileBackendConfig
        | RestApiBackendConfig
        | WebSocketBackendConfig
        | DatabaseBackendConfig
    ] = Field(default_factory=list)

    # Singleton settings
    enable_singleton: bool = Field(
        default=False, description="Enable singleton pattern"
    )
    singleton_name: str = Field(
        default="default", description="Singleton instance name"
    )

    model_config = ConfigDict(
        extra="ignore", use_enum_values=True, validate_assignment=True
    )

    @classmethod
    def from_env(cls, prefix: str = "LOGGER_") -> "GlobalLoggerConfig":
        """Create configuration from environment variables."""
        # Use an object-typed mapping to satisfy mypy when filling mixed types
        env_vars: dict[str, object] = {}

        # Map environment variables to config fields
        env_mapping = {
            f"{prefix}APP_NAME": "app_name",
            f"{prefix}ENVIRONMENT": "environment",
            f"{prefix}VERSION": "version",
            f"{prefix}LEVEL": "default_level",
            f"{prefix}CORRELATION_HEADER": "correlation_id_header",
            f"{prefix}ENABLE_CORRELATION": "enable_correlation_ids",
            f"{prefix}ENABLE_STRUCTURED": "enable_structured_context",
            f"{prefix}MAX_CONTEXT_SIZE": "max_context_size",
            f"{prefix}QUEUE_SIZE": "async_queue_size",
            f"{prefix}ENABLE_METRICS": "enable_performance_metrics",
            f"{prefix}ENABLE_SANITIZATION": "enable_sanitization",
            f"{prefix}ENABLE_SINGLETON": "enable_singleton",
            f"{prefix}SINGLETON_NAME": "singleton_name",
        }

        for env_var, config_field in env_mapping.items():
            value = os.getenv(env_var)
            if value is None:
                continue
            # Typed conversions
            if config_field in {
                "enable_correlation_ids",
                "enable_structured_context",
                "enable_performance_metrics",
                "enable_sanitization",
                "enable_singleton",
            }:
                env_vars[config_field] = value.lower() in {"true", "1", "yes", "on"}
            elif config_field in {"max_context_size", "async_queue_size"}:
                env_vars[config_field] = int(value)
            elif config_field == "default_level":
                env_vars[config_field] = LogLevel(value.lower())
            else:
                env_vars[config_field] = value

        # Handle sensitive fields
        sensitive_fields_env = os.getenv(f"{prefix}SENSITIVE_FIELDS")
        if sensitive_fields_env:
            env_vars["sensitive_fields"] = [
                field.strip() for field in sensitive_fields_env.split(",")
            ]

        # Construct from mapping via Pydantic for proper typing
        return cls.model_validate(env_vars)

    @model_validator(mode="after")
    def validate_config(self) -> "GlobalLoggerConfig":
        """Validate the complete configuration."""
        if not self.backends:
            # Add default console backend
            self.backends = [ConsoleBackendConfig(name="default_console")]

        # Validate backend names are unique
        backend_names = [backend.name for backend in self.backends]
        if len(backend_names) != len(set(backend_names)):
            raise JPYLoggerConfigurationError(
                message="Backend names must be unique",
                config_section="backends",
            )

        return self


class LoggerConfig(BaseModel):
    """Logger instance configuration."""

    name: str = Field(..., description="Logger name/identifier")
    level: LogLevel | None = Field(
        default=None,
        description="Override global level",
    )
    backends: list[str] | None = Field(
        default=None,
        description="Backend names to use (None = use all global backends)",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Default context",
    )
    correlation_id: str | None = Field(default=None, description="Fixed correlation ID")

    model_config = ConfigDict(extra="allow", use_enum_values=True)


# Factory functions for common configurations
def create_development_config() -> GlobalLoggerConfig:
    """Create development environment configuration."""
    return GlobalLoggerConfig(
        environment="development",
        default_level=LogLevel.DEBUG,
        backends=[
            ConsoleBackendConfig(
                name="dev_console", colors=True, format=LogFormat.CONSOLE
            )
        ],
    )


def create_production_config() -> GlobalLoggerConfig:
    """Create production environment configuration."""
    return GlobalLoggerConfig(
        environment="production",
        default_level=LogLevel.INFO,
        enable_performance_metrics=True,
        backends=[
            FileBackendConfig(
                name="prod_file",
                # Use a relative, writable default to avoid permission issues
                # in environments where creating system directories is not allowed.
                file_path=Path("logs/app.log"),
                format=LogFormat.JSON,
                max_size_mb=100,
                backup_count=10,
            )
        ],
    )


def create_cloud_config(api_url: str, api_key: str) -> GlobalLoggerConfig:
    """Create cloud logging configuration."""
    return GlobalLoggerConfig(
        environment="cloud",
        default_level=LogLevel.INFO,
        backends=[
            RestApiBackendConfig(
                name="cloud_api",
                base_url=api_url,
                security=SecurityConfig(
                    level=SecurityLevel.API_KEY,
                    api_key=api_key,
                ),
                batch_strategy=BatchStrategy.HYBRID,
            )
        ],
    )
