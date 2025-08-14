"""Core logger implementation following SOLID principles.

This module provides the public runtime API for structured logging used by
``jinpy-utils``. It includes a high-level :class:`Logger` with both
asynchronous and synchronous operations, a lightweight singleton-aware
manager (:class:`LoggerManager`) for global configuration and instance
lifecycle, as well as a set of convenience module-level functions for common
workflows.

Docstrings in this module follow the Google-style format to integrate
seamlessly with mkdocstrings' Python handler. Sections such as ``Args``,
``Returns``, ``Raises``, and ``Examples`` are included where appropriate to
enable high-quality, auto-generated API documentation.

Design highlights:

- Thread-safe global manager and instance registry
- Optional singleton behavior per configuration
- Async and sync logging with a background queue when supported by backends
- Structured entries enriched with source metadata and correlation IDs
- Performance metrics and basic back-pressure via bounded queues
- Context binding utilities and convenience helpers

Examples:
    Basic usage
    -----------
    >>> from jinpy_utils.logger import get_logger, set_global_config, create_development_config
    >>> set_global_config(create_development_config())
    >>> logger = get_logger("my_app")
    >>> logger.info("Application started", {"version": "1.0.0"})

    Async usage
    ----------
    >>> import asyncio
    >>> from jinpy_utils.logger import get_logger
    >>> async def main():
    ...     logger = get_logger("my_app")
    ...     await logger.ainfo("Processing async task")
    ...
    >>> asyncio.run(main())
"""

import asyncio
import inspect
import sys
import threading
import uuid
import weakref
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager, suppress
from typing import Any, ClassVar, Optional

from jinpy_utils.logger.backends import BackendFactory, BackendInterface, LogEntry
from jinpy_utils.logger.config import GlobalLoggerConfig, LoggerConfig
from jinpy_utils.logger.enums import LogLevel
from jinpy_utils.logger.exceptions import (
    JPYLoggerConfigurationError,
    JPYLoggerError,
    JPYLoggerPerformanceError,
)
from jinpy_utils.utils.timing import get_current_datetime


class LoggerManager:
    """Manage global logger configuration and instances.

    The manager coordinates a process-wide registry of :class:`Logger`
    instances and provides a single place to set and retrieve the global
    configuration. It supports optional singleton behavior so repeated calls
    to :meth:`get_logger` for the same name return the same instance when
    enabled in the global configuration.

    Thread-safety:
        All registry mutations are guarded by an internal lock. Reading
        operations are safe for concurrent use.
    """

    _instance: Optional["LoggerManager"] = None
    _lock = threading.Lock()
    _instances: ClassVar[dict[str, "Logger"]] = {}
    _global_config: GlobalLoggerConfig | None = None

    def __new__(cls) -> "LoggerManager":
        """Create or return the singleton instance.

        Returns:
            LoggerManager: The process-wide singleton instance.
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the manager on first construction.

        This method is idempotent and safe to call multiple times; the
        initialization block runs only once per process.
        """
        if not getattr(self, "_initialized", False):
            self._initialized = True
            self._cleanup_registry: set[weakref.ReferenceType] = set()
            self._background_tasks: set[asyncio.Task] = set()

    def set_global_config(self, config: GlobalLoggerConfig) -> None:
        """Set the global logger configuration.

        Args:
            config: The global configuration to apply to the manager and all
                current and future :class:`Logger` instances.
        """
        with self._lock:
            self._global_config = config

            # Update existing loggers if needed
            for logger in self._instances.values():
                logger._update_global_config(config)

    def get_global_config(self) -> GlobalLoggerConfig | None:
        """Return the current global configuration if set.

        Returns:
            GlobalLoggerConfig | None: The active global configuration, or
            ``None`` if not configured yet.
        """
        return self._global_config

    def get_logger(
        self,
        name: str,
        config: LoggerConfig | None = None,
        force_new: bool = False,
    ) -> "Logger":
        """Get or create a :class:`Logger` instance.

        Behavior depends on the global configuration:
        - If singleton mode is enabled and ``force_new`` is ``False`` (default),
          a cached instance for ``name`` is returned if present.
        - Otherwise a new instance is created.

        Args:
            name: Name of the logger instance.
            config: Optional per-logger configuration. If omitted, a default
                :class:`LoggerConfig` is created with the given ``name``.
            force_new: When ``True``, always create a new instance even if
                singleton mode is enabled.

        Returns:
            Logger: The logger instance.

        Raises:
            JPYLoggerConfigurationError: If the global configuration is not set
                via :meth:`set_global_config` prior to this call, or if no
                enabled backends are available.
        """
        if not self._global_config:
            raise JPYLoggerConfigurationError(
                message="Global configuration not set. Call set_global_config() first.",
                config_section="global",
            )

        # Check if singleton is enabled and instance exists
        if (
            self._global_config.enable_singleton
            and not force_new
            and name in self._instances
        ):
            return self._instances[name]

        # Create new instance
        logger = Logger(
            name,
            config or LoggerConfig(name=name),
            self._global_config,
        )

        # Store if singleton is enabled or explicitly requested
        if self._global_config.enable_singleton or not force_new:
            with self._lock:
                self._instances[name] = logger

                # Register for cleanup
                ref = weakref.ref(logger, self._cleanup_instance)
                self._cleanup_registry.add(ref)

        return logger

    def _cleanup_instance(self, ref: weakref.ReferenceType) -> None:
        """Cleanup dead references.

        Args:
            ref: A weak reference to a :class:`Logger` instance that has been
                garbage collected.
        """
        self._cleanup_registry.discard(ref)

    def shutdown_all(self) -> None:
        """Shutdown all logger instances.

        If a running event loop is detected, asynchronous ``close`` operations
        are scheduled for each logger; otherwise, they are executed using
        ``asyncio.run``. This ensures cleanup occurs in both synchronous and
        asynchronous application contexts.

        This method is idempotent and safe to call multiple times.
        """
        with self._lock:
            for logger in list(self._instances.values()):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    asyncio.run(logger.close())
                else:
                    task = loop.create_task(logger.close())
                    self._background_tasks.add(task)
                    task.add_done_callback(self._background_tasks.discard)
                    # best-effort: do not await here
            self._instances.clear()
            self._cleanup_registry.clear()

    def get_all_loggers(self) -> list["Logger"]:
        """Return a snapshot of all active logger instances.

        Returns:
            list[Logger]: A list of currently registered loggers.
        """
        with self._lock:
            return list(self._instances.values())


class Logger:
    """High-performance structured logger with async and sync APIs.

    The :class:`Logger` encapsulates configuration, backends, and operational
    policy for structured logging. It supports context binding, correlation IDs,
    asynchronous processing (when supported by the configured backends), and
    exposes convenience helpers for both sync and async application flows.

    Args:
        name: Logical name of the logger instance, typically the module or
            component name.
        config: Per-instance configuration model.
        global_config: Global configuration applied to all loggers via
            :class:`LoggerManager`.

    Attributes:
        name (str): The logger name.
        config (LoggerConfig): The logger-specific configuration.
        global_config (GlobalLoggerConfig): The active global configuration.
        _context (dict[str, Any]): Baseline structured context bound to the
            logger.
        _correlation_id (str | None): The current correlation identifier.
        _backends (list[BackendInterface]): Active backend instances.

    Examples:
        Basic usage
        -----------
        >>> from jinpy_utils.logger import Logger, LoggerManager
        >>> from jinpy_utils.logger.config import GlobalLoggerConfig
        >>> global_config = GlobalLoggerConfig.from_env()
        >>> LoggerManager().set_global_config(global_config)
        >>> logger = Logger.get_logger("example")
        >>> logger.info("Started", {"version": "1.0.0"})

        Context binding
        ---------------
        >>> with logger.context(user_id=123):
        ...     logger.error("Something happened")
    """

    def __init__(
        self,
        name: str,
        config: LoggerConfig,
        global_config: GlobalLoggerConfig,
    ):
        """
        Initialize logger instance.

        Args:
            name: Logger name
            config: Logger-specific configuration
            global_config: Global logger configuration
        """
        self.name = name
        self.config = config
        self.global_config = global_config

        # State management
        self._closed = False
        self._context: dict[str, Any] = config.context.copy()
        self._correlation_id = config.correlation_id

        # Performance tracking
        self._stats: dict[str, Any] = {
            "messages_logged": 0,
            "messages_dropped": 0,
            "bytes_processed": 0,
            "start_time": get_current_datetime(),
            "last_log_time": None,
        }

        # Initialize backends
        self._backends: list[BackendInterface] = []
        self._initialize_backends()

        # Async processing
        self._async_queue: asyncio.Queue | None = None
        self._processor_task: asyncio.Task | None = None
        self._setup_async_processing()

        # Security and sanitization
        self._sensitive_fields = set(global_config.sensitive_fields)

    def _initialize_backends(self) -> None:
        """Initialize backends based on configuration."""
        try:
            # Determine which backends to use
            if self.config.backends:
                # Use specific backends
                backend_configs = [
                    backend
                    for backend in self.global_config.backends
                    if backend.name in self.config.backends and backend.enabled
                ]
            else:
                # Use all enabled global backends
                backend_configs = [
                    backend
                    for backend in self.global_config.backends
                    if backend.enabled
                ]

            if not backend_configs:
                raise JPYLoggerConfigurationError(
                    message="No enabled backends found",
                    config_section="backends",
                )

            # Create backend instances
            for backend_config in backend_configs:
                try:
                    backend = BackendFactory.create_backend(backend_config)
                    self._backends.append(backend)
                except Exception as e:
                    raise JPYLoggerConfigurationError(
                        message=f"Failed to initialize backend {backend_config.name}: {e}",
                        config_section="backends",
                        config_value=backend_config.name,
                    ) from e

        except Exception as e:
            raise JPYLoggerError(
                message=f"Backend initialization failed: {e}",
                logger_name=self.name,
                operation="initialize_backends",
            ) from e

    def _setup_async_processing(self) -> None:
        """Setup async processing queue and background task if supported.

        When at least one backend reports async capability, a bounded queue is
        created and a background task is started if a running event loop is
        present. Otherwise, the task is created later on first async usage.
        """
        if any(hasattr(backend, "_async_capable") for backend in self._backends):
            self._async_queue = asyncio.Queue(
                maxsize=self.global_config.async_queue_size
            )
            try:
                asyncio.get_running_loop()
                self._processor_task = asyncio.create_task(
                    self._process_async_queue(),
                )
            except RuntimeError:
                # No running loop; task will be created lazily by caller if needed
                self._processor_task = None

    async def _process_async_queue(self) -> None:
        """Process async logging queue."""
        while not self._closed:
            try:
                # Get entry with timeout to allow periodic cleanup
                if self._async_queue is None:
                    raise ValueError("self._async_queue can not be None")

                entry = await asyncio.wait_for(
                    self._async_queue.get(),
                    timeout=1.0,
                )

                await self._write_to_backends_async(entry)
                self._async_queue.task_done()

            except TimeoutError:
                continue
            except Exception as e:
                self._handle_processing_error(e)

    def _handle_processing_error(self, error: Exception) -> None:
        """Handle async processing errors.

        Errors are counted and emitted to stderr to avoid recursive logging.
        """
        self._stats["messages_dropped"] = int(self._stats["messages_dropped"]) + 1

        # Log to stderr to avoid recursion
        print(f"Logger {self.name} processing error: {error}", file=sys.stderr)

    def _get_effective_level(self) -> LogLevel:
        """Return the effective log level considering global defaults."""
        return self.config.level or self.global_config.default_level

    def _should_log(self, level: LogLevel) -> bool:
        """Return whether a message at ``level`` should be emitted."""
        return level >= self._get_effective_level()

    def _sanitize_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Sanitize sensitive fields from the provided context.

        Sanitization behavior is controlled by the global configuration and
        will redact values for keys matching any configured sensitive token.

        Args:
            context: Arbitrary structured context to sanitize.

        Returns:
            dict[str, Any]: A sanitized copy of ``context``.
        """
        if not self.global_config.enable_sanitization:
            return context

        sanitized = {}
        for key, value in context.items():
            if any(sensitive in key.lower() for sensitive in self._sensitive_fields):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value

        return sanitized

    def _create_log_entry(
        self,
        level: LogLevel,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> LogEntry:
        """Create a structured :class:`LogEntry` with context and metadata.

        Merges bound context with provided context, applies sanitization, and
        enriches the entry with source information and a correlation ID.

        Args:
            level: Log level for the entry.
            message: Human-readable message for the entry.
            context: Optional structured context specific to this call.

        Returns:
            LogEntry: A fully-populated structured log entry.
        """
        # Merge contexts: instance -> method parameter
        merged_context = self._context.copy()
        if context:
            # Check context size limit
            context_str = str(context)
            if len(context_str) > self.global_config.max_context_size:
                context = {
                    "_context_truncated": True,
                    "_original_size": len(context_str),
                    "_truncated_at": get_current_datetime().isoformat(),
                }

            merged_context.update(context)

        # Sanitize context
        if merged_context:
            merged_context = self._sanitize_context(merged_context)

        # Generate correlation ID if needed
        correlation_id = self._correlation_id
        if self.global_config.enable_correlation_ids and not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Get caller information
        frame = inspect.currentframe()
        caller_frame = frame.f_back.f_back if frame and frame.f_back else None

        module_name = None
        function_name = None
        line_number = None

        if caller_frame:
            module_name = caller_frame.f_globals.get("__name__")
            function_name = caller_frame.f_code.co_name
            line_number = caller_frame.f_lineno

        return LogEntry(
            timestamp=get_current_datetime(),
            level=level,
            message=message,
            logger_name=self.name,
            correlation_id=correlation_id,
            context=merged_context,
            module=module_name,
            function=function_name,
            line_number=line_number,
        )

    async def _write_to_backends_async(self, entry: LogEntry) -> None:
        """Write entry to all backends asynchronously."""
        tasks = []
        for backend in self._backends:
            if backend.is_healthy():
                tasks.append(self._safe_backend_write_async(backend, entry))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_backend_write_async(
        self, backend: BackendInterface, entry: LogEntry
    ) -> None:
        """Safely write to backend with error handling."""
        try:
            await backend.write_async(entry)
        except Exception as e:
            self._stats["messages_dropped"] = int(self._stats["messages_dropped"]) + 1
            # Log backend error without recursion
            print(f"Backend {backend.name} error: {e}", file=sys.stderr)

    def _write_to_backends_sync(self, entry: LogEntry) -> None:
        """Write the entry to all configured backends synchronously."""
        for backend in self._backends:
            try:
                if backend.is_healthy():
                    backend.write_sync(entry)
            except Exception as e:
                self._stats["messages_dropped"] = (
                    int(self._stats["messages_dropped"]) + 1
                )
                # Log backend error without recursion
                print(f"Backend {backend.name} error: {e}", file=sys.stderr)

    def _update_stats(self, entry: LogEntry) -> None:
        """Update internal counters and performance metrics for ``entry``."""
        self._stats["messages_logged"] = int(self._stats["messages_logged"]) + 1
        self._stats["bytes_processed"] = int(self._stats["bytes_processed"]) + len(
            str(entry.to_dict())
        )
        self._stats["last_log_time"] = get_current_datetime()

        # Performance monitoring
        if self.global_config.enable_performance_metrics:
            current_time = get_current_datetime()
            if self._stats["last_log_time"] is not None:
                time_diff = (
                    current_time - self._stats["last_log_time"]
                ).total_seconds()
                if time_diff > 1.0:  # Alert if logging takes too long
                    raise JPYLoggerPerformanceError(
                        message="Logging performance degraded",
                        logger_name=self.name,
                        performance_metric="log_latency",
                        threshold_value=1.0,
                        actual_value=time_diff,
                    )

    # Synchronous logging methods
    def log(
        self,
        level: LogLevel,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Log a message at the specified level synchronously.

        Args:
            level: The severity level for the message.
            message: The log message content.
            context: Optional structured context merged into the bound
                context for this call. Large contexts are truncated in a
                controlled manner.

        Raises:
            JPYLoggerError: If logging fails at runtime.
        """
        if not self._should_log(level) or self._closed:
            return

        try:
            entry = self._create_log_entry(level, message, context)
            self._write_to_backends_sync(entry)
            self._update_stats(entry)
        except Exception as e:
            raise JPYLoggerError(
                message=f"Synchronous logging failed: {e}",
                logger_name=self.name,
                operation="log",
            ) from e

    def trace(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log a TRACE-level message synchronously.

        Args:
            message: The log message content.
            context: Optional structured context for this call.
        """
        self.log(LogLevel.TRACE, message, context)

    def debug(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log a DEBUG-level message synchronously.

        Args:
            message: The log message content.
            context: Optional structured context for this call.
        """
        self.log(LogLevel.DEBUG, message, context)

    def info(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log an INFO-level message synchronously.

        Args:
            message: The log message content.
            context: Optional structured context for this call.
        """
        self.log(LogLevel.INFO, message, context)

    def warning(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log a WARNING-level message synchronously.

        Args:
            message: The log message content.
            context: Optional structured context for this call.
        """
        self.log(LogLevel.WARNING, message, context)

    def error(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log an ERROR-level message synchronously.

        Args:
            message: The log message content.
            context: Optional structured context for this call.
        """
        self.log(LogLevel.ERROR, message, context)

    def critical(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log a CRITICAL-level message synchronously.

        Args:
            message: The log message content.
            context: Optional structured context for this call.
        """
        self.log(LogLevel.CRITICAL, message, context)

    # Asynchronous logging methods
    async def alog(
        self, level: LogLevel, message: str, context: dict[str, Any] | None = None
    ) -> None:
        """Log a message at the specified level asynchronously.

        Args:
            level: The severity level for the message.
            message: The log message content.
            context: Optional structured context merged into the bound
                context for this call.

        Raises:
            JPYLoggerError: If logging fails at runtime.
        """
        if not self._should_log(level) or self._closed:
            return

        try:
            entry = self._create_log_entry(level, message, context)

            # Use async queue if available and not full
            if self._async_queue and not self._async_queue.full():
                await self._async_queue.put(entry)
            else:
                # Fallback to direct write
                await self._write_to_backends_async(entry)

            self._update_stats(entry)
        except Exception as e:
            raise JPYLoggerError(
                message=f"Asynchronous logging failed: {e}",
                logger_name=self.name,
                operation="alog",
            ) from e

    async def atrace(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log a TRACE-level message asynchronously."""
        await self.alog(LogLevel.TRACE, message, context)

    async def adebug(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log a DEBUG-level message asynchronously."""
        await self.alog(LogLevel.DEBUG, message, context)

    async def ainfo(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log an INFO-level message asynchronously."""
        await self.alog(LogLevel.INFO, message, context)

    async def awarning(
        self, message: str, context: dict[str, Any] | None = None
    ) -> None:
        """Log a WARNING-level message asynchronously."""
        await self.alog(LogLevel.WARNING, message, context)

    async def aerror(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Log an ERROR-level message asynchronously."""
        await self.alog(LogLevel.ERROR, message, context)

    async def acritical(
        self, message: str, context: dict[str, Any] | None = None
    ) -> None:
        """Log a CRITICAL-level message asynchronously."""
        await self.alog(LogLevel.CRITICAL, message, context)

    # Context management
    @contextmanager
    def context(self, **kwargs: Any) -> Generator[None, None, None]:
        """Temporarily bind structured context for nested log calls.

        All keyword arguments provided are merged into the logger's bound
        context for the duration of the ``with`` block.

        Args:
            **kwargs: Key-value pairs to add to the bound context.

        Examples:
            >>> with logger.context(user_id=123, request_id="abcd"):
            ...     logger.info("processing")
        """
        old_context = self._context.copy()
        self._context.update(kwargs)
        try:
            yield
        finally:
            self._context = old_context

    @asynccontextmanager
    async def acontext(self, **kwargs: Any) -> AsyncGenerator[None, None]:
        """Temporarily bind structured context in asynchronous flows.

        Args:
            **kwargs: Key-value pairs to add to the bound context.

        Examples:
            >>> async with logger.acontext(user_id=123):
            ...     await logger.ainfo("processing")
        """
        old_context = self._context.copy()
        self._context.update(kwargs)
        try:
            yield
        finally:
            self._context = old_context

    def bind(self, **kwargs: Any) -> "Logger":
        """Return a child logger with additional bound context.

        Args:
            **kwargs: Context key-value pairs to bind permanently to the child
                logger's baseline context.

        Returns:
            Logger: A new logger instance inheriting configuration and the
            current context plus the provided key-value pairs.
        """
        child_config = LoggerConfig(
            name=f"{self.name}.child",
            level=self.config.level,
            backends=self.config.backends,
            context={**self._context, **kwargs},
            correlation_id=self._correlation_id,
        )

        return Logger(child_config.name, child_config, self.global_config)

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set a correlation identifier for this logger instance.

        Correlation IDs help tie together related log entries across
        components, requests, or processes.
        """
        self._correlation_id = correlation_id

    def get_correlation_id(self) -> str | None:
        """Return the current correlation identifier, if any."""
        return self._correlation_id

    def set_level(self, level: LogLevel) -> None:
        """Set the log level for this logger instance."""
        self.config.level = level

    def get_level(self) -> LogLevel:
        """Return the current effective log level for this instance."""
        return self._get_effective_level()

    def is_enabled_for(self, level: LogLevel) -> bool:
        """Return whether logging is enabled for the given ``level``."""
        return level >= self._get_effective_level()

    # Performance and maintenance
    async def flush(self) -> None:
        """Flush all pending log entries across async and backend buffers.

        When async processing is enabled, this waits for the internal queue to
        drain and then awaits any backend ``flush`` implementations.
        """
        if self._async_queue:
            await self._async_queue.join()

        # Flush all backends
        flush_tasks = []
        for backend in self._backends:
            if hasattr(backend, "flush"):
                flush_tasks.append(backend.flush())

        if flush_tasks:
            await asyncio.gather(*flush_tasks, return_exceptions=True)

    def get_stats(self) -> dict[str, Any]:
        """Return a snapshot of logger statistics.

        Returns:
            dict[str, Any]: Statistics including counters like
            ``messages_logged``, ``messages_dropped``, ``bytes_processed``, and
            derived metrics such as ``uptime_seconds`` and backend health
            information.
        """
        stats = self._stats.copy()
        stats["backend_count"] = len(self._backends)
        stats["healthy_backends"] = sum(1 for b in self._backends if b.is_healthy())
        start_time = self._stats["start_time"]
        stats["uptime_seconds"] = (get_current_datetime() - start_time).total_seconds()
        return stats

    def get_backend_stats(self) -> dict[str, dict[str, Any]]:
        """Return statistics for all configured backends keyed by name."""
        return {
            backend.name: backend.get_stats()
            for backend in self._backends
            if hasattr(backend, "get_stats")
        }

    def _update_global_config(self, config: GlobalLoggerConfig) -> None:
        """Update the logger instance when the global configuration changes."""
        self.global_config = config
        self._sensitive_fields = set(config.sensitive_fields)

    async def close(self) -> None:
        """Close the logger and cleanup resources.

        Cancels internal background tasks (if any), flushes all buffers, and
        closes each backend. Safe to call multiple times.
        """
        if self._closed:
            return

        self._closed = True

        # Cancel async processor
        if self._processor_task:
            self._processor_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._processor_task

        # Flush and close all backends
        await self.flush()
        close_tasks = []
        for backend in self._backends:
            close_tasks.append(backend.close())

        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)

    # Class methods for convenience
    @classmethod
    def get_logger(
        cls, name: str, config: LoggerConfig | None = None, force_new: bool = False
    ) -> "Logger":
        """Get a logger instance via the global :class:`LoggerManager`.

        This is a convenience wrapper around
        :meth:`LoggerManager.get_logger`.

        Args:
            name: Name of the logger instance.
            config: Optional per-logger configuration.
            force_new: When ``True``, always create a new instance even if
                singleton mode is enabled.

        Returns:
            Logger: The logger instance.
        """
        return LoggerManager().get_logger(name, config, force_new)

    @classmethod
    def set_global_config(cls, config: GlobalLoggerConfig) -> None:
        """Set the global configuration via the :class:`LoggerManager`."""
        LoggerManager().set_global_config(config)

    @classmethod
    def from_env(cls, name: str, env_prefix: str = "LOGGER_") -> "Logger":
        """Create a :class:`Logger` from environment variables.

        Args:
            name: Name of the logger instance.
            env_prefix: Prefix used to read environment variables for
                configuration.

        Returns:
            Logger: The configured logger instance.
        """
        global_config = GlobalLoggerConfig.from_env(env_prefix)
        cls.set_global_config(global_config)
        return cls.get_logger(name)

    def __del__(self) -> None:
        """Avoid async work in finalizer.

        Resource cleanup should be explicit via ``close()`` or
        ``LoggerManager.shutdown_all()``. Doing asynchronous work in
        ``__del__`` is unreliable and may emit warnings depending on
        interpreter shutdown timing and event loop state.
        """
        return None


# Convenience functions
def get_logger(
    name: str, config: LoggerConfig | None = None, force_new: bool = False
) -> Logger:
    """Get a :class:`Logger` instance.

    Convenience wrapper around :meth:`Logger.get_logger` for callers that
    prefer module-level functions.

    Args:
        name: Name of the logger instance.
        config: Optional per-logger configuration.
        force_new: When ``True``, always create a new instance even if
            singleton mode is enabled.

    Returns:
        Logger: The logger instance.
    """
    return Logger.get_logger(name, config, force_new)


def set_global_config(config: GlobalLoggerConfig) -> None:
    """Set the global logger configuration.

    This forwards to :meth:`Logger.set_global_config` for convenience.

    Args:
        config: The global configuration to apply.
    """
    Logger.set_global_config(config)


def configure_from_env(env_prefix: str = "LOGGER_") -> None:
    """Configure the global logger from environment variables.

    Args:
        env_prefix: Prefix used to read environment variables for
            configuration (defaults to ``"LOGGER_"``).
    """
    config = GlobalLoggerConfig.from_env(env_prefix)
    set_global_config(config)


def shutdown_all_loggers() -> None:
    """Shutdown all logger instances via :class:`LoggerManager`."""
    LoggerManager().shutdown_all()
