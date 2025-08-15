"""Tests for jinpy_utils.cache.core."""

import pytest

from jinpy_utils.cache.config import CacheManagerConfig, MemoryCacheConfig
from jinpy_utils.cache.core import (
    AsyncCacheClient,
    Cache,
    CacheClient,
    CacheManager,
    get_cache,
    get_cache_manager,
)
from jinpy_utils.cache.exceptions import CacheConfigurationError


class TestCacheManager:
    def test_default_initializes_memory_backend(self) -> None:
        mgr = CacheManager()  # may reuse singleton
        mgr = get_cache_manager(CacheManagerConfig())
        assert mgr.get("missing") is None

    def test_custom_backends_and_default_selection(self, tmp_path) -> None:
        cfg = CacheManagerConfig(
            backends=[MemoryCacheConfig(name="m1")],
            default_backend="m1",
        )
        mgr = get_cache_manager(cfg)
        with mgr.using() as cache:
            assert isinstance(cache, CacheClient)
            cache.set("k", 1)
            assert cache.get("k") == 1

    def test_invalid_default_backend_name_raises(self) -> None:
        cfg = CacheManagerConfig(backends=[MemoryCacheConfig(name="m")], default_backend="nope")
        with pytest.raises(CacheConfigurationError):
            _ = get_cache_manager(cfg)

    def test_no_enabled_backends_raises(self) -> None:
        cfg = CacheManagerConfig(backends=[MemoryCacheConfig(name="m", enabled=False)])
        with pytest.raises(CacheConfigurationError):
            _ = get_cache_manager(cfg)

    def test_reconfigure_selects_first_as_default_when_none(self) -> None:
        # When default_backend is None, the first enabled backend becomes default
        cfg = CacheManagerConfig(backends=[MemoryCacheConfig(name="first")])
        mgr = get_cache_manager(cfg)
        # should not raise when getting backend without name
        assert mgr.get_backend() is not None


class TestCacheSyncAndAsyncAPI:
    def test_sync_api(self) -> None:
        mgr = get_cache_manager(CacheManagerConfig(backends=[MemoryCacheConfig(name="m")] , default_backend="m"))
        c = Cache(manager=mgr)
        c.set("a", {"b": 1})
        assert c.get("a") == {"b": 1}
        assert c.exists("a") is True
        c.delete("a")
        assert c.get("a") is None
        c.set_many({"x": 1, "y": 2})
        got = c.get_many(["x", "y", "z"])
        assert got == {"x": 1, "y": 2, "z": None}
        c.delete_many(["x", "y"])  # type: ignore[arg-type]
        assert c.get("x") is None
        assert c.incr("n") == 1
        assert c.decr("n") == 0
        c.touch("n", 1)
        t = c.ttl("n")
        assert t is None or t >= 0
        assert isinstance(c.is_healthy(), bool)
        c.close()

    @pytest.mark.asyncio
    async def test_async_api_and_context(self) -> None:
        mgr = get_cache_manager(CacheManagerConfig(backends=[MemoryCacheConfig(name="m")] , default_backend="m"))
        async with mgr.ausing() as ac:
            assert isinstance(ac, AsyncCacheClient)
            await ac.aset("k", 1)
            assert await ac.aget("k") == 1
            await ac.adelete("k")
            assert await ac.aget("k") is None
            await ac.aset_many({"a": 1, "b": 2})
            got = await ac.aget_many(["a", "b", "c"])
            assert got == {"a": 1, "b": 2, "c": None}
            assert await ac.aincr("n") == 1
            assert await ac.adecr("n") == 0
            await ac.atouch("n", 1)
            t = await ac.attl("n")
            assert t is None or t >= 0
            assert isinstance(await ac.ais_healthy(), bool)
        await mgr.aclose()

    def test_close_specific_backend_and_manager_helpers(self) -> None:
        mgr = get_cache_manager(CacheManagerConfig(backends=[MemoryCacheConfig(name="m")], default_backend="m"))
        # Manager helpers delegate correctly for specific backend
        mgr.set("x", 1, backend="m")
        assert mgr.get("x", backend="m") == 1
        mgr.clear(backend="m")
        mgr.close(backend="m")

    @pytest.mark.asyncio
    async def test_aclose_specific_backend(self) -> None:
        mgr = get_cache_manager(CacheManagerConfig(backends=[MemoryCacheConfig(name="m")], default_backend="m"))
        await mgr.aclose(backend="m")


class TestHelpers:
    def test_get_cache_and_manager(self) -> None:
        c = get_cache()
        assert isinstance(c, Cache)
        m = get_cache_manager()
        assert isinstance(m, CacheManager)
