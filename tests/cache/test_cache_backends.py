"""Tests for jinpy_utils.cache.backends (one file per module).

Covers:
- BaseBackend sync delegations via Memory/File
- MemoryCacheBackend functionality and edge cases
- FileCacheBackend functionality and edge cases
- RedisCacheBackend success and error paths with stubbed client
- CacheBackendFactory creation and error handling
"""

from typing import Any
from unittest.mock import patch

import pytest

from jinpy_utils.cache.backends import (
    CacheBackendFactory,
    FileCacheBackend,
    MemoryCacheBackend,
)
from jinpy_utils.cache.config import (
    FileCacheConfig,
    MemoryCacheConfig,
    RedisCacheConfig,
)
from jinpy_utils.cache.enums import CacheBackendType
from jinpy_utils.cache.exceptions import (
    CacheBackendError,
    CacheConnectionError,
    CacheKeyError,
)


class TestBaseBackendSyncDelegates:
    def test_memory_sync_wrappers(self) -> None:
        be = MemoryCacheBackend(MemoryCacheConfig(name="m"))
        # set/get
        be.set("k", {"a": 1})
        assert be.get("k") == {"a": 1}
        assert be.exists("k") is True
        # bulk ops
        be.set_many({"x": 1, "y": 2})
        assert be.get_many(["x", "y", "z"]) == {"x": 1, "y": 2, "z": None}
        be.delete_many(["x", "y"])  # type: ignore[arg-type]
        assert be.get("x") is None
        # arithmetic and ttl
        assert be.incr("n") == 1
        assert be.decr("n") == 0
        be.touch("n", 1)
        t = be.ttl("n")
        assert t is None or t >= 0
        # lifecycle
        assert be.is_healthy() is True
        be.clear()
        be.delete("n")
        be.close()

    def test_file_sync_wrappers(self, tmp_path) -> None:
        cfg = FileCacheConfig(name="f", directory=tmp_path)
        be = FileCacheBackend(cfg)
        be.set("a", 1)
        assert be.get("a") == 1
        assert be.exists("a") is True
        be.set_many({"b": 2})
        assert be.get_many(["a", "b"]) == {"a": 1, "b": 2}
        be.delete_many(["a", "b"])  # type: ignore[arg-type]
        assert be.get("a") is None
        assert be.is_healthy() is True
        be.clear()
        be.close()


class TestMemoryCacheBackend:
    @pytest.mark.asyncio
    async def test_set_get_exists_delete_and_clear(self) -> None:
        backend = MemoryCacheBackend(MemoryCacheConfig(name="m"))
        await backend.aset("k", {"v": 1})
        assert await backend.aget("k") == {"v": 1}
        assert await backend.aexists("k") is True
        await backend.adelete("k")
        assert await backend.aget("k") is None
        await backend.aclear()

    @pytest.mark.asyncio
    async def test_ttl_touch_and_bulk(self) -> None:
        backend = MemoryCacheBackend(MemoryCacheConfig(name="m"))
        await backend.aset("k", "v", ttl=0.1)
        remaining = await backend.attl("k")
        assert remaining is None or remaining >= 0
        await backend.atouch("k", 0.2)
        t2 = await backend.attl("k")
        assert t2 is None or t2 >= 0
        await backend.aset_many({"a": 1, "b": 2})
        got = await backend.aget_many(["a", "b", "c"])
        assert got == {"a": 1, "b": 2, "c": None}
        await backend.adelete_many(["a", "b"]) 
        assert await backend.aget("a") is None
        assert await backend.aget("b") is None

    @pytest.mark.asyncio
    async def test_incr_decr_and_validation(self) -> None:
        backend = MemoryCacheBackend(MemoryCacheConfig(name="m"))
        assert await backend.aincr("c") == 1
        assert await backend.adecr("c") == 0
        with pytest.raises(CacheKeyError):
            await backend.aincr("c", amount=-1)
        with pytest.raises(CacheKeyError):
            await backend.adecr("c", amount=-1)

    @pytest.mark.asyncio
    async def test_thread_unsafe_mode_and_expiry(self) -> None:
        be = MemoryCacheBackend(MemoryCacheConfig(name="m", thread_safe=False))
        await be.aset("e", 1, ttl=0)
        assert await be.aget("e") is None
        assert await be.aexists("e") is False
        await be.aset("k1", 1)
        await be.aset("k2", 2, ttl=0)
        got = await be.aget_many(["k1", "k2"])  # k2 should be purged
        assert got["k1"] == 1
        assert got["k2"] is None


class TestFileCacheBackend:
    @pytest.mark.asyncio
    async def test_file_set_get_exists_delete_and_clear(self, tmp_path) -> None:
        backend = FileCacheBackend(FileCacheConfig(name="f", directory=tmp_path))
        await backend.aset("k", {"x": 1}, ttl=0.2)
        assert await backend.aexists("k") is True
        assert await backend.aget("k") == {"x": 1}
        ttl = await backend.attl("k")
        assert ttl is None or ttl >= 0
        await backend.adelete("k")
        assert await backend.aget("k") is None
        await backend.aclear()

    @pytest.mark.asyncio
    async def test_file_incr_decr_and_negative_amount(self, tmp_path) -> None:
        be = FileCacheBackend(FileCacheConfig(name="f", directory=tmp_path))
        assert await be.aincr("n") == 1
        assert await be.adecr("n") == 0
        with pytest.raises(CacheKeyError):
            await be.aincr("n", amount=-1)
        with pytest.raises(CacheKeyError):
            await be.adecr("n", amount=-1)

    @pytest.mark.asyncio
    async def test_file_exists_with_expired_ttl_deletes(self, tmp_path) -> None:
        be = FileCacheBackend(FileCacheConfig(name="f", directory=tmp_path))
        await be.aset("k", 1)
        p = be._path_for("k")
        p.with_suffix(p.suffix + ".ttl").write_text("0")
        assert await be.aexists("k") is False
        assert not p.exists()

    @pytest.mark.asyncio
    async def test_file_eviction_on_max_entries(self, tmp_path) -> None:
        be = FileCacheBackend(
            FileCacheConfig(name="f", directory=tmp_path, max_entries=1)
        )
        await be.aset("k1", 1)
        await be.aset("k2", 2)
        assert await be.aget("k1") is None
        assert await be.aget("k2") == 2

    @pytest.mark.asyncio
    async def test_file_atouch_noop_when_missing(self, tmp_path) -> None:
        be = FileCacheBackend(FileCacheConfig(name="f", directory=tmp_path))
        await be.atouch("missing", 10)

    @pytest.mark.asyncio
    async def test_file_deserialization_error_on_corruption(self, tmp_path) -> None:
        be = FileCacheBackend(FileCacheConfig(name="f", directory=tmp_path))
        # Corrupt the stored file content to simulate external file tampering
        path = be._path_for("bad")
        path.write_bytes(b"\xff\xfe\xfd")
        with pytest.raises(CacheBackendError):
            await be.aget("bad")


class _DummyRedisClient:
    def __init__(self, decode: bool = False) -> None:
        self.decode = decode
        self._store: dict[str, Any] = {}
        self._ttl: dict[str, int] = {}

    async def ping(self):
        return True

    async def aclose(self):
        return None

    async def get(self, k: str):
        return self._store.get(k)

    async def set(self, k: str, v: Any, ex: Any | None = None):
        self._store[k] = v
        if ex:
            self._ttl[k] = int(ex)

    async def delete(self, *keys: str):
        for k in keys:
            self._store.pop(k, None)

    async def exists(self, k: str):
        return 1 if k in self._store else 0

    async def scan(self, cursor: int = 0, match: str = "*"):
        return 0, list(self._store.keys())

    async def mget(self, keys: list[str]):
        return [self._store.get(k) for k in keys]

    def pipeline(self):
        client = self

        class _Pipe:
            def __init__(self) -> None:
                self.ops: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

            def set(self, *a, **kw):
                self.ops.append(("set", a, kw))

            async def execute(self):
                for _name, a, kw in self.ops:
                    await client.set(*a, **kw)

        return _Pipe()

    async def incrby(self, k: str, amount: int):
        self._store[k] = int(self._store.get(k, 0)) + amount
        return self._store[k]

    async def decrby(self, k: str, amount: int):
        self._store[k] = int(self._store.get(k, 0)) - amount
        return self._store[k]

    async def ttl(self, k: str):
        return self._ttl.get(k, -1)

    async def expire(self, k: str, ttl: int):
        self._ttl[k] = ttl


class TestRedisCacheBackend:
    @pytest.mark.asyncio
    async def test_success_paths_with_decode_true_and_false(self) -> None:
        cfg_bytes = RedisCacheConfig(
            name="r1", url="redis://localhost:6379/0", decode_responses=False
        )
        cfg_text = RedisCacheConfig(
            name="r2", url="redis://localhost:6379/0", decode_responses=True
        )

        with patch(
            "jinpy_utils.cache.backends.aioredis.from_url",
            return_value=_DummyRedisClient(False),
        ):
            from jinpy_utils.cache.backends import RedisCacheBackend

            be = RedisCacheBackend(cfg_bytes)
            await be.aset("k", {"a": 1})
            assert await be.aget("k") == {"a": 1}
            assert await be.aexists("k") is True
            await be.adelete_many(["nope"])  # noop
            await be.aset_many({"x": 1, "y": 2})
            got = await be.aget_many(["x", "y", "z"])
            assert got == {"x": 1, "y": 2, "z": None}
            assert await be.aincr("n") == 1
            assert await be.adecr("n") == 0
            await be.atouch("k", 5)
            t = await be.attl("k")
            assert t is None or t >= 0
            assert await be.ais_healthy() is True
            await be.aclose()

        with patch(
            "jinpy_utils.cache.backends.aioredis.from_url",
            return_value=_DummyRedisClient(True),
        ):
            from jinpy_utils.cache.backends import RedisCacheBackend

            be2 = RedisCacheBackend(cfg_text)
            await be2.aset("k", {"a": 1})
            assert await be2.aget("k") == {"a": 1}
            await be2.aclear()

    @pytest.mark.asyncio
    async def test_error_paths_raise_backend_errors(self) -> None:
        class Raising:
            async def ping(self):
                return True

            async def get(self, *_a, **_k):
                raise RuntimeError("get err")

            async def set(self, *_a, **_k):
                raise RuntimeError("set err")

            async def delete(self, *_a, **_k):
                raise RuntimeError("del err")

            async def exists(self, *_a, **_k):
                raise RuntimeError("exists err")

            async def scan(self, *_a, **_k):
                raise RuntimeError("scan err")

            async def mget(self, *_a, **_k):
                raise RuntimeError("mget err")

            def pipeline(self):
                class P:
                    def set(self, *_a, **_k):
                        pass

                    async def execute(self):
                        raise RuntimeError("pipe err")

                return P()

            async def incrby(self, *_a, **_k):
                raise RuntimeError("incr err")

            async def decrby(self, *_a, **_k):
                raise RuntimeError("decr err")

            async def ttl(self, *_a, **_k):
                raise RuntimeError("ttl err")

            async def expire(self, *_a, **_k):
                raise RuntimeError("expire err")

            async def aclose(self):
                return None

        with patch(
            "jinpy_utils.cache.backends.aioredis.from_url", return_value=Raising()
        ):
            from jinpy_utils.cache.backends import RedisCacheBackend

            be = RedisCacheBackend(
                RedisCacheConfig(name="r", url="redis://localhost:6379/0")
            )
            with pytest.raises(CacheBackendError):
                await be.aget("k")
            with pytest.raises(CacheBackendError):
                await be.aset("k", 1)
            with pytest.raises(CacheBackendError):
                await be.adelete("k")
            with pytest.raises(CacheBackendError):
                await be.aexists("k")
            with pytest.raises(CacheBackendError):
                await be.aclear()
            with pytest.raises(CacheBackendError):
                await be.aget_many(["a"]) 
            with pytest.raises(CacheBackendError):
                await be.aset_many({"a": 1})
            with pytest.raises(CacheBackendError):
                await be.adelete_many(["a"]) 
            with pytest.raises(CacheBackendError):
                await be.aincr("n")
            with pytest.raises(CacheBackendError):
                await be.adecr("n")
            with pytest.raises(CacheBackendError):
                await be.attl("k")
            with pytest.raises(CacheBackendError):
                await be.atouch("k", 5)

    @pytest.mark.asyncio
    async def test_connect_failure_raises_connection_error(self) -> None:
        async def _bad_from_url(*_a: Any, **_k: Any):  # type: ignore
            raise RuntimeError("boom")

        with patch(
            "jinpy_utils.cache.backends.aioredis.from_url", side_effect=_bad_from_url
        ):
            from jinpy_utils.cache.backends import RedisCacheBackend

            with pytest.raises(CacheConnectionError):
                be = RedisCacheBackend(
                    RedisCacheConfig(name="r", url="redis://localhost:6379/0")
                )
                await be.aget("k")

    @pytest.mark.asyncio
    async def test_clear_scan_without_keys_multiple_iterations(self) -> None:
        class ScanOnly:
            def __init__(self) -> None:
                self.calls = 0

            async def ping(self):
                return True

            async def scan(self, cursor: int = 0, match: str = "*"):
                self.calls += 1
                if self.calls == 1:
                    return 1, []  # not done yet
                return 0, []

            async def delete(self, *_a, **_k):
                pass

        with patch(
            "jinpy_utils.cache.backends.aioredis.from_url", return_value=ScanOnly()
        ):
            from jinpy_utils.cache.backends import RedisCacheBackend

            be = RedisCacheBackend(
                RedisCacheConfig(name="r", url="redis://localhost:6379/0")
            )
            await be.aclear()


class TestBackendFactory:
    def test_factory_creates_supported_and_unsupported(self) -> None:
        m = CacheBackendFactory.create(MemoryCacheConfig(name="m"))
        assert isinstance(m, MemoryCacheBackend)
        with patch(
            "jinpy_utils.cache.backends.RedisCacheBackend.__init__", return_value=None
        ):
            r = CacheBackendFactory.create(
                RedisCacheConfig(name="r", url="redis://localhost:6379/0")
            )
            assert r is not None
        with pytest.raises(CacheBackendError):

            class Dummy:  # type: ignore
                def __init__(self) -> None:
                    self.name = "x"

            CacheBackendFactory.create(Dummy())  # type: ignore[arg-type]
