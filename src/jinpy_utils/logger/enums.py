"""
Enumerations for the logger module.

This module defines all enumeration types used throughout the logger system
for better type safety and consistency.
"""

from enum import Enum


class LogLevel(str, Enum):
    """Log level enumeration with string values."""

    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @property
    def numeric_value(self) -> int:
        """Get numeric value for log level comparison."""
        mapping = {
            self.TRACE: 5,
            self.DEBUG: 10,
            self.INFO: 20,
            self.WARNING: 30,
            self.ERROR: 40,
            self.CRITICAL: 50,
        }
        return mapping[self]

    def __ge__(self, other: "LogLevel") -> bool:  # type:ignore
        """Greater than or equal comparison."""
        return self.numeric_value >= other.numeric_value

    def __gt__(self, other: "LogLevel") -> bool:  # type:ignore
        """Greater than comparison."""
        return self.numeric_value > other.numeric_value

    def __le__(self, other: "LogLevel") -> bool:  # type:ignore
        """Less than or equal comparison."""
        return self.numeric_value <= other.numeric_value

    def __lt__(self, other: "LogLevel") -> bool:  # type:ignore
        """Less than comparison."""
        return self.numeric_value < other.numeric_value


class BackendType(str, Enum):
    """Supported logging backend types."""

    CONSOLE = "console"
    FILE = "file"
    ROTATING_FILE = "rotating_file"
    REST_API = "rest_api"
    DATABASE = "database"
    WEBSOCKET = "websocket"
    SYSLOG = "syslog"
    MEMORY = "memory"
    REDIS = "redis"
    KAFKA = "kafka"
    ELASTICSEARCH = "elasticsearch"


class LogFormat(str, Enum):
    """Log output format options."""

    JSON = "json"
    CONSOLE = "console"
    PLAIN = "plain"
    STRUCTURED = "structured"
    CEF = "cef"  # Common Event Format
    GELF = "gelf"  # Graylog Extended Log Format


class CompressionType(str, Enum):
    """Compression types for log files."""

    NONE = "none"
    GZIP = "gzip"
    BZIP2 = "bzip2"
    XZ = "xz"
    ZIP = "zip"


class SecurityLevel(str, Enum):
    """Security levels for logging operations."""

    NONE = "none"
    BASIC = "basic"
    TLS = "tls"
    MUTUAL_TLS = "mutual_tls"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"


class ConnectionState(str, Enum):
    """Connection states for backends."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
    CLOSED = "closed"


class BatchStrategy(str, Enum):
    """Batching strategies for backends."""

    SIZE_BASED = "size_based"
    TIME_BASED = "time_based"
    HYBRID = "hybrid"
    IMMEDIATE = "immediate"


class RetryStrategy(str, Enum):
    """Retry strategies for failed operations."""

    NONE = "none"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"
