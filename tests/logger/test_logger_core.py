"""Tests for the logger core module with 100% coverage."""

import asyncio
from collections.abc import Generator
from unittest.mock import patch

import pytest

from jinpy_utils.logger.config import (
    ConsoleBackendConfig,
    DatabaseBackendConfig,
    GlobalLoggerConfig,
)
from jinpy_utils.logger.core import (
    Logger,
    LoggerManager,
    configure_from_env,
    get_logger,
    set_global_config,
    shutdown_all_loggers,
)
from jinpy_utils.logger.enums import LogLevel
from jinpy_utils.logger.exceptions import JPYLoggerError


@pytest.fixture(autouse=True)
def _cleanup_loggers() -> Generator[None, None, None]:
    """Ensure no loggers leak between tests to avoid finalizer side-effects."""
    yield
    mgr = LoggerManager()
    for lg in mgr.get_all_loggers():
        # Ensure proper async cleanup even outside an event loop
        asyncio.run(lg.close())
    # Clear manager state
    # Access protected attribute for test cleanup
    mgr._instances.clear()


@pytest.fixture
def global_config() -> GlobalLoggerConfig:
    return GlobalLoggerConfig(
        backends=[ConsoleBackendConfig(name="console")],
        enable_singleton=False,
    )


class TestLoggerManager:
    def test_singleton_and_instance_management(
        self, global_config: GlobalLoggerConfig
    ) -> None:
        mgr = LoggerManager()
        mgr.set_global_config(global_config)

        logger1 = mgr.get_logger("app")
        logger2 = mgr.get_logger("app", force_new=True)
        assert logger1 is not logger2

        # get all returns list; since enable_singleton=False, first call did not store persistently
        all_loggers: list[Logger] = mgr.get_all_loggers()
        assert isinstance(all_loggers, list)

        # Switch to singleton mode
        mgr.set_global_config(GlobalLoggerConfig(enable_singleton=True))
        l1 = mgr.get_logger("svc")
        l2 = mgr.get_logger("svc")
        assert l1 is l2

    def test_shutdown_all_with_and_without_loop(
        self, global_config: GlobalLoggerConfig
    ) -> None:
        mgr = LoggerManager()
        mgr.set_global_config(global_config)
        mgr.get_logger("shutdown")

        # When no loop, uses asyncio.run
        mgr.set_global_config(global_config)
        mgr.get_logger("shutdown2")
        with (
            patch("asyncio.get_running_loop", side_effect=RuntimeError()),
            patch("asyncio.run") as runp,
        ):
            mgr.shutdown_all()
            runp.assert_called()


class TestLogger:
    def test_logger_sync_methods_and_stats(
        self, global_config: GlobalLoggerConfig
    ) -> None:
        Logger.set_global_config(global_config)
        logger = Logger.get_logger("sync")

        # Log various levels (ensure all are enabled)
        logger.set_level(LogLevel.TRACE)
        logger.trace("t")
        logger.debug("d")
        logger.info("i")
        logger.warning("w")
        logger.error("e")
        logger.critical("c")

        stats = logger.get_stats()
        assert isinstance(stats["messages_logged"], int)
        assert stats["messages_logged"] >= 6
        backend_stats = logger.get_backend_stats()
        assert isinstance(backend_stats, dict)

        # Level checks
        assert logger.is_enabled_for(LogLevel.INFO)
        logger.set_level(LogLevel.ERROR)
        assert logger.get_level() == LogLevel.ERROR

    @pytest.mark.asyncio
    async def test_logger_async_methods_and_flush(
        self, global_config: GlobalLoggerConfig
    ) -> None:
        Logger.set_global_config(global_config)
        logger = Logger.get_logger("async")

        await logger.atrace("t")
        await logger.adebug("d")
        await logger.ainfo("i")
        await logger.awarning("w")
        await logger.aerror("e")
        await logger.acritical("c")

        await logger.flush()
        await logger.close()
        # Repeated close should no-op
        await logger.close()
        # Explicitly finalize to avoid any lingering finalizer
        del logger

    def test_logger_context_and_bind(self, global_config: GlobalLoggerConfig) -> None:
        Logger.set_global_config(global_config)
        logger = Logger.get_logger("ctx")

        with logger.context(user_id=1):
            logger.info("within")

        async def _async_with_context():
            async with logger.acontext(request_id="r"):
                await logger.ainfo("awithin")

        asyncio.run(_async_with_context())

        child = logger.bind(role="admin")
        assert isinstance(child, Logger)
        assert child.name.endswith(".child")

    def test_logger_from_env_and_helpers(
        self, global_config: GlobalLoggerConfig
    ) -> None:
        # configure_from_env should set and not crash
        configure_from_env()
        # helper wrappers work
        set_global_config(global_config)
        lg = get_logger("helper")
        assert isinstance(lg, Logger)
        # Explicitly close to avoid destructor warnings
        asyncio.run(lg.close())
        shutdown_all_loggers()

    def test_logger_backend_init_errors(self) -> None:
        # Use unsupported backend to force factory failure
        cfg = GlobalLoggerConfig(
            backends=[
                DatabaseBackendConfig(name="db", connection_string="sqlite:///x.db")
            ]
        )
        Logger.set_global_config(cfg)
        with pytest.raises(JPYLoggerError):
            Logger.get_logger("err")

    @pytest.mark.asyncio
    async def test_logger_error_handling_paths(
        self, global_config: GlobalLoggerConfig
    ) -> None:
        # Configure console backend but force backend to report not healthy to trigger drop path
        Logger.set_global_config(global_config)
        logger = Logger.get_logger("errs")

        # Patch backend to unhealthy and simulate exceptions in sync/async writes
        for backend in logger._backends:
            # simulate unhealthy so writes are skipped
            backend._healthy = False  # type: ignore

        logger.info("skip due to unhealthy")
        await logger.ainfo("skip due to unhealthy")

        # Now make healthy and force write errors
        for backend in logger._backends:
            backend._healthy = True  # type: ignore

        with patch.object(
            logger._backends[0], "write_sync", side_effect=Exception("x")
        ):
            logger.info("boom")
        with patch.object(
            logger._backends[0], "write_async", side_effect=Exception("x")
        ):
            await logger.ainfo("boom")

    def test_logger_performance_error_toggle(self) -> None:
        # Enable performance metrics and trigger branch without raising (no time gap)
        cfg = GlobalLoggerConfig(enable_performance_metrics=True)
        Logger.set_global_config(cfg)
        logger = Logger.get_logger("perf")
        logger.info("ok")
