# jpy_utils/cache/core.py

from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncGenerator, Generator, Mapping
from contextlib import asynccontextmanager, contextmanager, suppress
from typing import Any

from .backends import BaseBackend, CacheBackendFactory
from .config import CacheManagerConfig, MemoryCacheConfig
from .exceptions import CacheConfigurationError


class CacheManager:
    """
    Singleton-aware cache manager with async/sync APIs.

    Responsibilities:
    - Initialize and manage multiple cache backends (memory, file, redis, etc.)
    - Provide a consistent sync and async API delegating to selected backend
    - Enforce configuration via Pydantic models
    - Follow SOLID principles (separation of concerns, single responsibility)
    - 12-Factor: environment-driven config handled by the Pydantic config layer

    Usage:
        manager = CacheManager()  # uses defaults (in-memory)
        manager.set("key", {"a": 1}, ttl=60)
        value = manager.get("key")

        # Async
        await manager.aset("k", "v", ttl=30)
        v = await manager.aget("k")
    """

    _instance: CacheManager | None = None
    _lock = threading.Lock()

    def __new__(
        cls,
        config: CacheManagerConfig | None = None,
    ) -> CacheManager:
        # Strict singleton: if instance exists, return it;
        # first call constructs.
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: CacheManagerConfig | None = None) -> None:
        # Idempotent init to support singleton semantics.
        if getattr(self, "_initialized", False):
            # If new config provided later, allow reconfigure explicitly
            if config is not None:
                self._reconfigure(config)
            return

        self._initialized = True
        self.config = config or CacheManagerConfig()
        self._backends: dict[str, BaseBackend] = {}
        self._default_backend_name: str | None = self.config.default_backend
        self._initialize_backends()

    def _reconfigure(self, config: CacheManagerConfig) -> None:
        """
        Reconfigure the manager with a new configuration.

        Safely closes previous backends and re-initializes with the new config.
        """
        self.close()  # best-effort close of existing
        self.config = config
        self._backends.clear()
        self._default_backend_name = self.config.default_backend
        self._initialize_backends()

    def _initialize_backends(self) -> None:
        """
        Initialize and register all enabled backends per configuration.

        Ensures a default backend is available.
        """
        # Provide a default in-memory backend if none configured.
        if not self.config.backends:
            default = MemoryCacheConfig(name="default_memory")
            self.config.backends = [default]
            self._default_backend_name = "default_memory"

        for backend_cfg in self.config.backends:
            if getattr(backend_cfg, "enabled", True):
                backend = CacheBackendFactory.create(backend_cfg)
                self._backends[backend_cfg.name] = backend

        if not self._backends:
            raise CacheConfigurationError(
                "No enabled cache backends configured",
                config_section="backends",
            )

        if not self._default_backend_name:
            # pick first enabled backend as default
            self._default_backend_name = next(iter(self._backends.keys()))

        if self._default_backend_name not in self._backends:
            raise CacheConfigurationError(
                "Default backend name not found",
                config_section="default_backend",
                config_value=str(self._default_backend_name),
            )

    def get_backend(self, name: str | None = None) -> BaseBackend:
        """
        Retrieve a backend by name, or the default if name is None.
        """
        bname = name or self._default_backend_name
        if not bname or bname not in self._backends:
            raise CacheConfigurationError(
                "Requested backend not found",
                config_section="backend",
                config_value=str(bname),
            )
        return self._backends[bname]

    # --------------------------- Sync API --------------------------- #

    def get(self, key: str, *, backend: str | None = None) -> Any | None:
        return self.get_backend(backend).get(key)

    def set(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
        *,
        backend: str | None = None,
    ) -> None:
        self.get_backend(backend).set(key, value, ttl)

    def delete(self, key: str, *, backend: str | None = None) -> None:
        self.get_backend(backend).delete(key)

    def exists(self, key: str, *, backend: str | None = None) -> bool:
        return self.get_backend(backend).exists(key)

    def clear(self, *, backend: str | None = None) -> None:
        self.get_backend(backend).clear()

    def get_many(
        self, keys: list[str], *, backend: str | None = None
    ) -> dict[str, Any | None]:
        return self.get_backend(backend).get_many(keys)

    def set_many(
        self,
        items: dict[str, Any],
        ttl: float | None = None,
        *,
        backend: str | None = None,
    ) -> None:
        self.get_backend(backend).set_many(items, ttl)

    def delete_many(
        self,
        keys: list[str],
        *,
        backend: str | None = None,
    ) -> None:
        self.get_backend(backend).delete_many(keys)

    def incr(
        self,
        key: str,
        amount: int = 1,
        ttl: float | None = None,
        *,
        backend: str | None = None,
    ) -> int:
        return self.get_backend(backend).incr(key, amount, ttl)

    def decr(
        self,
        key: str,
        amount: int = 1,
        ttl: float | None = None,
        *,
        backend: str | None = None,
    ) -> int:
        return self.get_backend(backend).decr(key, amount, ttl)

    def ttl(self, key: str, *, backend: str | None = None) -> float | None:
        return self.get_backend(backend).ttl(key)

    def touch(
        self,
        key: str,
        ttl: float,
        *,
        backend: str | None = None,
    ) -> None:
        self.get_backend(backend).touch(key, ttl)

    def is_healthy(self, *, backend: str | None = None) -> bool:
        return self.get_backend(backend).is_healthy()

    def close(self, *, backend: str | None = None) -> None:
        """
        Close either a specific backend or all backends.
        """
        if backend is None:
            for b in self._backends.values():
                with suppress(Exception):
                    b.close()
        else:
            with suppress(Exception):
                self.get_backend(backend).close()

    # --------------------------- Async API --------------------------- #

    async def aget(
        self,
        key: str,
        *,
        backend: str | None = None,
    ) -> Any | None:
        return await self.get_backend(backend).aget(key)

    async def aset(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
        *,
        backend: str | None = None,
    ) -> None:
        await self.get_backend(backend).aset(key, value, ttl)

    async def adelete(self, key: str, *, backend: str | None = None) -> None:
        await self.get_backend(backend).adelete(key)

    async def aexists(self, key: str, *, backend: str | None = None) -> bool:
        return await self.get_backend(backend).aexists(key)

    async def aclear(self, *, backend: str | None = None) -> None:
        await self.get_backend(backend).aclear()

    async def aget_many(
        self, keys: list[str], *, backend: str | None = None
    ) -> dict[str, Any | None]:
        return await self.get_backend(backend).aget_many(keys)

    async def aset_many(
        self,
        items: dict[str, Any],
        ttl: float | None = None,
        *,
        backend: str | None = None,
    ) -> None:
        await self.get_backend(backend).aset_many(items, ttl)

    async def adelete_many(
        self, keys: list[str], *, backend: str | None = None
    ) -> None:
        await self.get_backend(backend).adelete_many(keys)

    async def aincr(
        self,
        key: str,
        amount: int = 1,
        ttl: float | None = None,
        *,
        backend: str | None = None,
    ) -> int:
        return await self.get_backend(backend).aincr(key, amount, ttl)

    async def adecr(
        self,
        key: str,
        amount: int = 1,
        ttl: float | None = None,
        *,
        backend: str | None = None,
    ) -> int:
        return await self.get_backend(backend).adecr(key, amount, ttl)

    async def attl(
        self,
        key: str,
        *,
        backend: str | None = None,
    ) -> float | None:
        return await self.get_backend(backend).attl(key)

    async def atouch(
        self,
        key: str,
        ttl: float,
        *,
        backend: str | None = None,
    ) -> None:
        await self.get_backend(backend).atouch(key, ttl)

    async def ais_healthy(self, *, backend: str | None = None) -> bool:
        return await self.get_backend(backend).ais_healthy()

    async def aclose(self, *, backend: str | None = None) -> None:
        """
        Close either a specific backend or all backends asynchronously.

        Note: Individual backends may only support sync close; this method
        will best-effort call async close if present,
        or fallback to sync close.
        """
        if backend is None:
            tasks: list[asyncio.Future | asyncio.Task] = []
            for b in self._backends.values():
                if hasattr(b, "aclose"):
                    tasks.append(asyncio.create_task(b.aclose()))
                else:
                    # Fallback to running sync close in a thread if needed
                    loop = asyncio.get_running_loop()
                    tasks.append(loop.run_in_executor(None, b.close))
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        else:
            b = self.get_backend(backend)
            if hasattr(b, "aclose"):
                await b.aclose()
            else:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, b.close)

    # ---------------------- Context Managers ------------------------ #

    @contextmanager
    def using(
        self,
        backend: str | None = None,
    ) -> Generator[CacheClient, None, None]:
        """
        Context manager yielding a CacheClient bound to a selected backend.

        Example:
            with manager.using("memory") as cache:
                cache.set("k", "v")
                v = cache.get("k")
        """
        client = CacheClient(self, backend)
        try:
            yield client
        finally:
            # No-op; backends are managed by the manager
            pass

    @asynccontextmanager
    async def ausing(
        self, backend: str | None = None
    ) -> AsyncGenerator[AsyncCacheClient, None]:
        """
        Async context manager yielding an AsyncCacheClient
        bound to a selected backend.

        Example:
            async with manager.ausing("redis") as cache:
                await cache.aset("k", "v")
                v = await cache.aget("k")
        """
        client = AsyncCacheClient(self, backend)
        try:
            yield client
        finally:
            # No-op; backends are managed by the manager
            pass


class CacheClient:
    """
    Thin synchronous facade over CacheManager bound to a specific backend.
    """

    def __init__(self, manager: CacheManager, backend: str | None) -> None:
        self._manager = manager
        self._backend = backend

    def get(self, key: str) -> Any | None:
        return self._manager.get(key, backend=self._backend)

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        self._manager.set(key, value, ttl, backend=self._backend)

    def delete(self, key: str) -> None:
        self._manager.delete(key, backend=self._backend)

    def exists(self, key: str) -> bool:
        return self._manager.exists(key, backend=self._backend)

    def clear(self) -> None:
        self._manager.clear(backend=self._backend)

    def get_many(self, keys: list[str]) -> dict[str, Any | None]:
        return self._manager.get_many(keys, backend=self._backend)

    def set_many(
        self,
        items: dict[str, Any],
        ttl: float | None = None,
    ) -> None:
        self._manager.set_many(items, ttl, backend=self._backend)

    def delete_many(self, keys: list[str]) -> None:
        self._manager.delete_many(keys, backend=self._backend)

    def incr(self, key: str, amount: int = 1, ttl: float | None = None) -> int:
        return self._manager.incr(key, amount, ttl, backend=self._backend)

    def decr(self, key: str, amount: int = 1, ttl: float | None = None) -> int:
        return self._manager.decr(key, amount, ttl, backend=self._backend)

    def ttl(self, key: str) -> float | None:
        return self._manager.ttl(key, backend=self._backend)

    def touch(self, key: str, ttl: float) -> None:
        self._manager.touch(key, ttl, backend=self._backend)

    def is_healthy(self) -> bool:
        return self._manager.is_healthy(backend=self._backend)


class AsyncCacheClient:
    """
    Thin asynchronous facade over CacheManager bound to a specific backend.
    """

    def __init__(self, manager: CacheManager, backend: str | None) -> None:
        self._manager = manager
        self._backend = backend

    async def aget(self, key: str) -> Any | None:
        return await self._manager.aget(key, backend=self._backend)

    async def aset(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
    ) -> None:
        await self._manager.aset(key, value, ttl, backend=self._backend)

    async def adelete(self, key: str) -> None:
        await self._manager.adelete(key, backend=self._backend)

    async def aexists(self, key: str) -> bool:
        return await self._manager.aexists(key, backend=self._backend)

    async def aclear(self) -> None:
        await self._manager.aclear(backend=self._backend)

    async def aget_many(self, keys: list[str]) -> dict[str, Any | None]:
        return await self._manager.aget_many(keys, backend=self._backend)

    async def aset_many(
        self,
        items: dict[str, Any],
        ttl: float | None = None,
    ) -> None:
        await self._manager.aset_many(items, ttl, backend=self._backend)

    async def adelete_many(self, keys: list[str]) -> None:
        await self._manager.adelete_many(keys, backend=self._backend)

    async def aincr(
        self,
        key: str,
        amount: int = 1,
        ttl: float | None = None,
    ) -> int:
        return await self._manager.aincr(
            key,
            amount,
            ttl,
            backend=self._backend,
        )

    async def adecr(
        self,
        key: str,
        amount: int = 1,
        ttl: float | None = None,
    ) -> int:
        return await self._manager.adecr(
            key,
            amount,
            ttl,
            backend=self._backend,
        )

    async def attl(self, key: str) -> float | None:
        return await self._manager.attl(key, backend=self._backend)

    async def atouch(self, key: str, ttl: float) -> None:
        await self._manager.atouch(key, ttl, backend=self._backend)

    async def ais_healthy(self) -> bool:
        return await self._manager.ais_healthy(backend=self._backend)


class Cache:
    """
    High-level cache facade API.

    This class delegates to a process-wide CacheManager instance under the hood
    and provides both sync and async methods for common operations.
    It is a thin wrapper that preserves
    the backend selection and promotes simple usage.

    Usage (sync):
        cache = Cache()  # uses default manager (singleton)
        cache.set("k", {"v": 1}, ttl=60)
        value = cache.get("k")

    Usage (async):
        cache = Cache()
        await cache.aset("k", "v", ttl=30)
        v = await cache.aget("k")
    """

    def __init__(
        self,
        backend: str | None = None,
        manager: CacheManager | None = None,
    ) -> None:
        self._manager = manager or CacheManager()
        self._backend = backend

    # --------------------------- Sync API --------------------------- #

    def get(self, key: str) -> Any | None:
        return self._manager.get(key, backend=self._backend)

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        self._manager.set(key, value, ttl, backend=self._backend)

    def delete(self, key: str) -> None:
        self._manager.delete(key, backend=self._backend)

    def exists(self, key: str) -> bool:
        return self._manager.exists(key, backend=self._backend)

    def clear(self) -> None:
        self._manager.clear(backend=self._backend)

    def get_many(self, keys: list[str]) -> dict[str, Any | None]:
        return self._manager.get_many(keys, backend=self._backend)

    def set_many(
        self,
        items: Mapping[str, Any],
        ttl: float | None = None,
    ) -> None:
        self._manager.set_many(dict(items), ttl, backend=self._backend)

    def delete_many(self, keys: list[str]) -> None:
        self._manager.delete_many(keys, backend=self._backend)

    def incr(self, key: str, amount: int = 1, ttl: float | None = None) -> int:
        return self._manager.incr(key, amount, ttl, backend=self._backend)

    def decr(self, key: str, amount: int = 1, ttl: float | None = None) -> int:
        return self._manager.decr(key, amount, ttl, backend=self._backend)

    def ttl(self, key: str) -> float | None:
        return self._manager.ttl(key, backend=self._backend)

    def touch(self, key: str, ttl: float) -> None:
        self._manager.touch(key, ttl, backend=self._backend)

    def is_healthy(self) -> bool:
        return self._manager.is_healthy(backend=self._backend)

    def close(self) -> None:
        self._manager.close(backend=self._backend)

    # --------------------------- Async API --------------------------- #

    async def aget(self, key: str) -> Any | None:
        return await self._manager.aget(key, backend=self._backend)

    async def aset(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
    ) -> None:
        await self._manager.aset(key, value, ttl, backend=self._backend)

    async def adelete(self, key: str) -> None:
        await self._manager.adelete(key, backend=self._backend)

    async def aexists(self, key: str) -> bool:
        return await self._manager.aexists(key, backend=self._backend)

    async def aclear(self) -> None:
        await self._manager.aclear(backend=self._backend)

    async def aget_many(self, keys: list[str]) -> dict[str, Any | None]:
        return await self._manager.aget_many(keys, backend=self._backend)

    async def aset_many(
        self, items: Mapping[str, Any], ttl: float | None = None
    ) -> None:
        await self._manager.aset_many(dict(items), ttl, backend=self._backend)

    async def adelete_many(self, keys: list[str]) -> None:
        await self._manager.adelete_many(keys, backend=self._backend)

    async def aincr(
        self,
        key: str,
        amount: int = 1,
        ttl: float | None = None,
    ) -> int:
        return await self._manager.aincr(
            key,
            amount,
            ttl,
            backend=self._backend,
        )

    async def adecr(
        self,
        key: str,
        amount: int = 1,
        ttl: float | None = None,
    ) -> int:
        return await self._manager.adecr(
            key,
            amount,
            ttl,
            backend=self._backend,
        )

    async def attl(self, key: str) -> float | None:
        return await self._manager.attl(key, backend=self._backend)

    async def atouch(self, key: str, ttl: float) -> None:
        await self._manager.atouch(key, ttl, backend=self._backend)

    async def ais_healthy(self) -> bool:
        return await self._manager.ais_healthy(backend=self._backend)

    async def aclose(self) -> None:
        await self._manager.aclose(backend=self._backend)


# Convenience functions mirroring the logger’s public helpers


def get_cache(backend: str | None = None) -> Cache:
    """
    Return a Cache facade bound to the given backend (or default).
    """
    return Cache(backend=backend)


def get_cache_manager(
    config: CacheManagerConfig | None = None,
) -> CacheManager:
    """
    Return the singleton CacheManager,
    optionally reconfiguring with a new config.
    Reconfiguration is applied if a non-None config is passed.
    """
    mgr = CacheManager()
    if config is not None:
        # Reconfigure existing instance
        mgr._reconfigure(config)  # type: ignore[attr-defined]
    return mgr
