from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import Any, Callable, ClassVar, Mapping, Tuple

import redis.asyncio as aioredis

from .config import FileCacheConfig, MemoryCacheConfig, RedisCacheConfig
from .enums import CacheBackendType, CacheOperation
from .exceptions import (
    CacheBackendError,
    CacheConnectionError,
    CacheException,
    CacheKeyError,
    CacheSerializationError,
)
from .interfaces import AsyncCacheInterface, CacheInterface
from .utils import (
    compute_expiry,
    default_serializer,
    normalize_key,
    remaining_ttl,
)


class BaseBackend(CacheInterface, AsyncCacheInterface):
    """Common backend base with serialization support."""

    _async_capable: ClassVar[bool] = True

    def __init__(
        self,
        name: str,
        serializer: Tuple[Callable[[Any], bytes], Callable[[bytes], Any]],
        default_ttl: float | None,
    ) -> None:
        self.name = name
        self._ser, self._de = serializer
        self._default_ttl = default_ttl

    # Sync API default: delegate to async if not overridden
    def get(self, key: str) -> Any | None:
        return asyncio.run(self.aget(key))

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        asyncio.run(self.aset(key, value, ttl))

    def delete(self, key: str) -> None:
        asyncio.run(self.adelete(key))

    def exists(self, key: str) -> bool:
        return asyncio.run(self.aexists(key))

    def clear(self) -> None:
        asyncio.run(self.aclear())

    def get_many(self, keys: list[str]) -> dict[str, Any | None]:
        return asyncio.run(self.aget_many(keys))

    def set_many(
        self, items: Mapping[str, Any], ttl: float | None = None
    ) -> None:  # noqa: E501
        asyncio.run(self.aset_many(items, ttl))

    def delete_many(self, keys: list[str]) -> None:
        asyncio.run(self.adelete_many(keys))

    def incr(self, key: str, amount: int = 1, ttl: float | None = None) -> int:
        return asyncio.run(self.aincr(key, amount, ttl))

    def decr(self, key: str, amount: int = 1, ttl: float | None = None) -> int:
        return asyncio.run(self.adecr(key, amount, ttl))

    def ttl(self, key: str) -> float | None:
        return asyncio.run(self.attl(key))

    def touch(self, key: str, ttl: float) -> None:
        asyncio.run(self.atouch(key, ttl))

    def is_healthy(self) -> bool:
        return asyncio.run(self.ais_healthy())

    def close(self) -> None:
        asyncio.run(self.aclose())


class MemoryCacheBackend(BaseBackend):
    """In-memory cache with optional size limit and TTL."""

    def __init__(self, config: MemoryCacheConfig) -> None:
        ser = default_serializer(config.serializer)
        super().__init__(config.name, ser, config.default_ttl)
        self._store: dict[str, tuple[bytes, float | None]] = {}
        self._lock = asyncio.Lock() if config.thread_safe else None
        self._max_entries = config.max_entries

    async def _with_lock(self, coro):
        if self._lock is None:
            return await coro
        async with self._lock:
            return await coro

    async def aget(self, key: str) -> Any | None:
        k = normalize_key(key)

        async def _get():
            entry = self._store.get(k)
            if not entry:
                return None
            data, expiry = entry
            if expiry is not None and remaining_ttl(expiry) == 0:
                self._store.pop(k, None)
                return None
            try:
                return self._de(data)
            except Exception as e:
                raise CacheSerializationError(
                    message=f"Deserialization failed: {e}",
                    cache_key=k,
                    backend_name=self.name,
                    operation=CacheOperation.GET,
                ) from e

        return await self._with_lock(_get())

    async def aset(
        self, key: str, value: Any, ttl: float | None = None
    ) -> None:  # noqa: E501
        k = normalize_key(key)
        expiry = compute_expiry(ttl if ttl is not None else self._default_ttl)

        async def _set():
            try:
                data = self._ser(value)
            except Exception as e:
                raise CacheSerializationError(
                    message=f"Serialization failed: {e}",
                    cache_key=k,
                    backend_name=self.name,
                    operation=CacheOperation.SET,
                ) from e
            self._store[k] = (data, expiry)
            if self._max_entries and len(self._store) > self._max_entries:
                # Simple FIFO eviction
                first_key = next(iter(self._store.keys()))
                self._store.pop(first_key, None)

        await self._with_lock(_set())

    async def adelete(self, key: str) -> None:
        k = normalize_key(key)

        async def _del():
            self._store.pop(k, None)

        await self._with_lock(_del())

    async def aexists(self, key: str) -> bool:
        k = normalize_key(key)

        async def _exists():
            entry = self._store.get(k)
            if not entry:
                return False
            _, expiry = entry
            if expiry is not None and remaining_ttl(expiry) == 0:
                self._store.pop(k, None)
                return False
            return True

        return await self._with_lock(_exists())

    async def aclear(self) -> None:
        async def _clear():
            self._store.clear()

        await self._with_lock(_clear())

    async def aget_many(self, keys: list[str]) -> dict[str, Any | None]:
        async def _get_many():
            result: dict[str, Any | None] = {}
            for key in keys:
                k = normalize_key(key)
                entry = self._store.get(k)
                if not entry:
                    result[key] = None
                    continue
                data, expiry = entry
                if expiry is not None and remaining_ttl(expiry) == 0:
                    self._store.pop(k, None)
                    result[key] = None
                    continue
                try:
                    result[key] = self._de(data)
                except Exception as e:
                    raise CacheSerializationError(
                        message=f"Deserialization failed: {e}",
                        cache_key=k,
                        backend_name=self.name,
                        operation=CacheOperation.GET,
                    ) from e
            return result

        return await self._with_lock(_get_many())

    async def aset_many(
        self, items: Mapping[str, Any], ttl: float | None = None
    ) -> None:
        async def _set_many():
            expiry_default = compute_expiry(ttl if ttl is not None else self._default_ttl)
            for k, v in items.items():
                nk = normalize_key(k)
                # Recompute expiry per item to reflect current time consistently
                expiry = expiry_default if ttl is not None or self._default_ttl is not None else None
                if ttl is not None and ttl <= 0:
                    expiry = compute_expiry(ttl)
                elif ttl is None and self._default_ttl is not None:
                    expiry = compute_expiry(self._default_ttl)
                try:
                    raw = self._ser(v)
                except Exception as e:
                    raise CacheSerializationError(
                        message=f"Serialization failed: {e}",
                        cache_key=nk,
                        backend_name=self.name,
                        operation=CacheOperation.SET,
                    ) from e
                self._store[nk] = (raw, expiry)
                if self._max_entries and len(self._store) > self._max_entries:
                    first_key = next(iter(self._store.keys()))
                    self._store.pop(first_key, None)

        await self._with_lock(_set_many())

    async def adelete_many(self, keys: list[str]) -> None:
        async def _del_many():
            for k in keys:
                nk = normalize_key(k)
                self._store.pop(nk, None)

        await self._with_lock(_del_many())

    async def aincr(
        self, key: str, amount: int = 1, ttl: float | None = None
    ) -> int:  # noqa: E501
        if amount < 0:
            raise CacheKeyError(
                "Amount must be non-negative",
                cache_key=key,
                backend_name=self.name,
                operation=CacheOperation.INCR,
            )
        val = await self.aget(key)
        new_val = (int(val) if val is not None else 0) + amount
        await self.aset(key, new_val, ttl)
        return new_val

    async def adecr(
        self, key: str, amount: int = 1, ttl: float | None = None
    ) -> int:  # noqa: E501
        if amount < 0:
            raise CacheKeyError(
                "Amount must be non-negative",
                cache_key=key,
                backend_name=self.name,
                operation=CacheOperation.DECR,
            )
        val = await self.aget(key)
        new_val = (int(val) if val is not None else 0) - amount
        await self.aset(key, new_val, ttl)
        return new_val

    async def attl(self, key: str) -> float | None:
        k = normalize_key(key)

        async def _ttl():
            entry = self._store.get(k)
            if not entry:
                return None
            _, expiry = entry
            return remaining_ttl(expiry)

        return await self._with_lock(_ttl())

    async def atouch(self, key: str, ttl: float) -> None:
        k = normalize_key(key)

        async def _touch():
            entry = self._store.get(k)
            if not entry:
                return
            data, _ = entry
            self._store[k] = (data, compute_expiry(ttl))

        await self._with_lock(_touch())

    async def ais_healthy(self) -> bool:
        return True

    async def aclose(self) -> None:
        await self.aclear()


class RedisCacheBackend(BaseBackend):
    """Async Redis backend. Requires redis-py[asyncio]."""

    def __init__(self, config: RedisCacheConfig) -> None:
        if aioredis is None:  # pragma: no cover
            raise CacheConnectionError(
                message="redis.asyncio is not available. Install 'redis>=4.2' package.",  # noqa: E501
                backend_name=config.name,
                backend_type=CacheBackendType.REDIS.value,
            )
        ser = default_serializer(config.serializer)
        super().__init__(config.name, ser, config.default_ttl)
        self._url = config.url
        self._decode = config.decode_responses
        self._pool_size = config.pool_size
        self._connect_timeout = config.connect_timeout
        self._command_timeout = config.command_timeout
        self._client: aioredis.Redis | None = None  # type: ignore

    async def _client_or_connect(self) -> "aioredis.Redis":
        if self._client is not None:
            return self._client
        try:
            self._client = aioredis.from_url(
                self._url,
                encoding="utf-8" if self._decode else None,
                decode_responses=self._decode,
                max_connections=self._pool_size,
                socket_connect_timeout=self._connect_timeout,
                socket_timeout=self._command_timeout,
            )
            # simple ping
            await self._client.ping()
            return self._client
        except Exception as e:
            raise CacheConnectionError(
                message=f"Redis connection failed: {e}",
                backend_name=self.name,
                backend_type=CacheBackendType.REDIS.value,
            ) from e

    async def aget(self, key: str) -> Any | None:
        k = normalize_key(key)
        cli = await self._client_or_connect()
        try:
            data = await cli.get(k)
            if data is None:
                return None
            if self._decode:
                # decode_responses True means data is str -> encode before deserialize if needed # noqa: E501
                raw = data.encode("utf-8")
            else:
                raw = data
            return self._de(raw)  # type: ignore[arg-type]
        except CacheException:
            raise
        except Exception as e:
            raise CacheBackendError(
                message=f"Redis GET failed: {e}",
                cache_key=k,
                backend_name=self.name,
                backend_type=CacheBackendType.REDIS.value,
            ) from e

    async def aset(
        self, key: str, value: Any, ttl: float | None = None
    ) -> None:  # noqa: E501
        k = normalize_key(key)
        cli = await self._client_or_connect()
        try:
            raw = self._ser(value)
            if self._decode:
                # store text when decode_responses is True
                await cli.set(
                    k,
                    raw.decode("utf-8"),
                    ex=ttl if ttl else self._default_ttl,
                )
            else:
                await cli.set(k, raw, ex=ttl if ttl else self._default_ttl)
        except Exception as e:
            raise CacheBackendError(
                message=f"Redis SET failed: {e}",
                cache_key=k,
                backend_name=self.name,
                backend_type=CacheBackendType.REDIS.value,
            ) from e

    async def adelete(self, key: str) -> None:
        k = normalize_key(key)
        cli = await self._client_or_connect()
        try:
            await cli.delete(k)
        except Exception as e:
            raise CacheBackendError(
                message=f"Redis DEL failed: {e}",
                cache_key=k,
                backend_name=self.name,
                backend_type=CacheBackendType.REDIS.value,
            ) from e

    async def aexists(self, key: str) -> bool:
        k = normalize_key(key)
        cli = await self._client_or_connect()
        try:
            return bool(await cli.exists(k))
        except Exception as e:
            raise CacheBackendError(
                message=f"Redis EXISTS failed: {e}",
                cache_key=k,
                backend_name=self.name,
                backend_type=CacheBackendType.REDIS.value,
            ) from e

    async def aclear(self) -> None:
        cli = await self._client_or_connect()
        try:
            # Use scan+delete to avoid flushing entire DB
            cursor: int = 0
            while True:
                cursor, keys = await cli.scan(cursor=cursor, match="*")
                if keys:
                    await cli.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            raise CacheBackendError(
                message=f"Redis CLEAR failed: {e}",
                backend_name=self.name,
                backend_type=CacheBackendType.REDIS.value,
            ) from e

    async def aget_many(self, keys: list[str]) -> dict[str, Any | None]:
        cli = await self._client_or_connect()
        nkeys = [normalize_key(k) for k in keys]
        try:
            values = await cli.mget(nkeys)
            result: dict[str, Any | None] = {}
            for k, v in zip(keys, values):
                if v is None:
                    result[k] = None
                else:
                    raw = v.encode("utf-8") if self._decode else v
                    result[k] = self._de(raw)  # type: ignore[arg-type]
            return result
        except Exception as e:
            raise CacheBackendError(
                message=f"Redis MGET failed: {e}",
                backend_name=self.name,
                backend_type=CacheBackendType.REDIS.value,
            ) from e

    async def aset_many(
        self, items: Mapping[str, Any], ttl: float | None = None
    ) -> None:
        cli = await self._client_or_connect()
        try:
            pipe = cli.pipeline()
            for k, v in items.items():
                nk = normalize_key(k)
                raw = self._ser(v)
                if self._decode:
                    pipe.set(
                        nk,
                        raw.decode("utf-8"),
                        ex=ttl if ttl else self._default_ttl,
                    )
                else:
                    pipe.set(nk, raw, ex=ttl if ttl else self._default_ttl)
            await pipe.execute()
        except Exception as e:
            raise CacheBackendError(
                message=f"Redis MSET failed: {e}",
                backend_name=self.name,
                backend_type=CacheBackendType.REDIS.value,
            ) from e

    async def adelete_many(self, keys: list[str]) -> None:
        cli = await self._client_or_connect()
        nkeys = [normalize_key(k) for k in keys]
        try:
            if nkeys:
                await cli.delete(*nkeys)
        except Exception as e:
            raise CacheBackendError(
                message=f"Redis DEL MANY failed: {e}",
                backend_name=self.name,
                backend_type=CacheBackendType.REDIS.value,
            ) from e

    async def aincr(
        self, key: str, amount: int = 1, ttl: float | None = None
    ) -> int:  # noqa: E501
        if amount < 0:
            raise CacheKeyError(
                "Amount must be non-negative",
                cache_key=key,
                backend_name=self.name,
                operation=CacheOperation.INCR,
            )
        cli = await self._client_or_connect()
        k = normalize_key(key)
        try:
            val = await cli.incrby(k, amount)
            if ttl is not None or self._default_ttl is not None:
                await cli.expire(
                    k, int(ttl if ttl is not None else self._default_ttl or 0)
                )
            return int(val)
        except Exception as e:
            raise CacheBackendError(
                message=f"Redis INCR failed: {e}",
                cache_key=k,
                backend_name=self.name,
                backend_type=CacheBackendType.REDIS.value,
            ) from e

    async def adecr(
        self, key: str, amount: int = 1, ttl: float | None = None
    ) -> int:  # noqa: E501
        if amount < 0:
            raise CacheKeyError(
                "Amount must be non-negative",
                cache_key=key,
                backend_name=self.name,
                operation=CacheOperation.DECR,
            )
        cli = await self._client_or_connect()
        k = normalize_key(key)
        try:
            val = await cli.decrby(k, amount)
            if ttl is not None or self._default_ttl is not None:
                await cli.expire(
                    k, int(ttl if ttl is not None else self._default_ttl or 0)
                )
            return int(val)
        except Exception as e:
            raise CacheBackendError(
                message=f"Redis DECR failed: {e}",
                cache_key=k,
                backend_name=self.name,
                backend_type=CacheBackendType.REDIS.value,
            ) from e

    async def attl(self, key: str) -> float | None:
        cli = await self._client_or_connect()
        k = normalize_key(key)
        try:
            t = await cli.ttl(k)
            if t is None or t < 0:
                return None
            return float(t)
        except Exception as e:
            raise CacheBackendError(
                message=f"Redis TTL failed: {e}",
                cache_key=k,
                backend_name=self.name,
                backend_type=CacheBackendType.REDIS.value,
            ) from e

    async def atouch(self, key: str, ttl: float) -> None:
        cli = await self._client_or_connect()
        k = normalize_key(key)
        try:
            await cli.expire(k, int(ttl))
        except Exception as e:
            raise CacheBackendError(
                message=f"Redis TOUCH failed: {e}",
                cache_key=k,
                backend_name=self.name,
                backend_type=CacheBackendType.REDIS.value,
            ) from e

    async def ais_healthy(self) -> bool:
        try:
            cli = await self._client_or_connect()
            pong = await cli.ping()
            return bool(pong)
        except Exception:
            return False

    async def aclose(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()  # type: ignore[attr-defined]
            finally:
                self._client = None


class FileCacheBackend(BaseBackend):
    """Simple file-based backend storing entries per file."""

    def __init__(self, config: FileCacheConfig) -> None:
        ser = default_serializer(config.serializer)
        super().__init__(config.name, ser, config.default_ttl)
        self._dir = config.directory
        self._ext = config.file_extension
        self._max_entries = config.max_entries
        self._lock = asyncio.Lock()

    def _path_for(self, key: str) -> Path:
        safe = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self._dir / f"{safe}{self._ext}"

    async def aget(self, key: str) -> Any | None:
        async with self._lock:
            p = self._path_for(normalize_key(key))
            if not p.exists():
                return None
            try:
                data = p.read_bytes()
                ttl_bytes = p.with_suffix(p.suffix + ".ttl")
                expiry: float | None = None
                if ttl_bytes.exists():
                    try:
                        expiry = float(ttl_bytes.read_text())
                    except Exception:
                        expiry = None
                if expiry is not None and remaining_ttl(expiry) == 0:
                    try:
                        p.unlink(missing_ok=True)
                        ttl_bytes.unlink(missing_ok=True)
                    finally:
                        return None
                return self._de(data)
            except Exception as e:
                raise CacheBackendError(
                    message=f"File GET failed: {e}",
                    cache_key=key,
                    backend_name=self.name,
                    backend_type=CacheBackendType.FILE.value,
                ) from e

    async def aset(
        self, key: str, value: Any, ttl: float | None = None
    ) -> None:  # noqa: E501
        async with self._lock:
            p = self._path_for(normalize_key(key))
            try:
                raw = self._ser(value)
                p.write_bytes(raw)
                ex = compute_expiry(
                    ttl if ttl is not None else self._default_ttl,
                )
                ttl_file = p.with_suffix(p.suffix + ".ttl")
                if ex is None:
                    ttl_file.unlink(missing_ok=True)
                else:
                    ttl_file.write_text(str(ex))
                if self._max_entries is not None:
                    # naive eviction: if too many files, remove oldest
                    files = sorted(
                        (f for f in self._dir.glob(f"*{self._ext}")),
                        key=lambda f: f.stat().st_mtime,
                    )
                    while len(files) > self._max_entries:
                        victim = files.pop(0)
                        victim.unlink(missing_ok=True)
                        tf = victim.with_suffix(victim.suffix + ".ttl")
                        tf.unlink(missing_ok=True)
            except Exception as e:
                raise CacheBackendError(
                    message=f"File SET failed: {e}",
                    cache_key=key,
                    backend_name=self.name,
                    backend_type=CacheBackendType.FILE.value,
                ) from e

    async def adelete(self, key: str) -> None:
        async with self._lock:
            p = self._path_for(normalize_key(key))
            try:
                p.unlink(missing_ok=True)
                p.with_suffix(p.suffix + ".ttl").unlink(missing_ok=True)
            except Exception as e:
                raise CacheBackendError(
                    message=f"File DEL failed: {e}",
                    cache_key=key,
                    backend_name=self.name,
                    backend_type=CacheBackendType.FILE.value,
                ) from e

    async def aexists(self, key: str) -> bool:
        async with self._lock:
            p = self._path_for(normalize_key(key))
            if not p.exists():
                return False
            ttl_file = p.with_suffix(p.suffix + ".ttl")
            expiry: float | None = None
            if ttl_file.exists():
                try:
                    expiry = float(ttl_file.read_text())
                except Exception:
                    expiry = None
            if expiry is not None and remaining_ttl(expiry) == 0:
                try:
                    p.unlink(missing_ok=True)
                    ttl_file.unlink(missing_ok=True)
                finally:
                    return False
            return True

    async def aclear(self) -> None:
        async with self._lock:
            for f in self._dir.glob(f"*{self._ext}"):
                try:
                    f.unlink(missing_ok=True)
                    f.with_suffix(f.suffix + ".ttl").unlink(missing_ok=True)
                except Exception:
                    # best-effort clear
                    pass

    async def aget_many(self, keys: list[str]) -> dict[str, Any | None]:
        result: dict[str, Any | None] = {}
        for k in keys:
            result[k] = await self.aget(k)
        return result

    async def aset_many(
        self, items: Mapping[str, Any], ttl: float | None = None
    ) -> None:
        for k, v in items.items():
            await self.aset(k, v, ttl)

    async def adelete_many(self, keys: list[str]) -> None:
        for k in keys:
            await self.adelete(k)

    async def aincr(
        self, key: str, amount: int = 1, ttl: float | None = None
    ) -> int:  # noqa: E501
        if amount < 0:
            raise CacheKeyError(
                "Amount must be non-negative",
                cache_key=key,
                backend_name=self.name,
                operation=CacheOperation.INCR,
            )
        val = await self.aget(key)
        new_val = (int(val) if val is not None else 0) + amount
        await self.aset(key, new_val, ttl)
        return new_val

    async def adecr(
        self, key: str, amount: int = 1, ttl: float | None = None
    ) -> int:  # noqa: E501
        if amount < 0:
            raise CacheKeyError(
                "Amount must be non-negative",
                cache_key=key,
                backend_name=self.name,
                operation=CacheOperation.DECR,
            )
        val = await self.aget(key)
        new_val = (int(val) if val is not None else 0) - amount
        await self.aset(key, new_val, ttl)
        return new_val

    async def attl(self, key: str) -> float | None:
        async with self._lock:
            p = self._path_for(normalize_key(key))
            ttl_file = p.with_suffix(p.suffix + ".ttl")
            if not ttl_file.exists():
                return None
            try:
                expiry = float(ttl_file.read_text())
                return remaining_ttl(expiry)
            except Exception:
                return None

    async def atouch(self, key: str, ttl: float) -> None:
        async with self._lock:
            p = self._path_for(normalize_key(key))
            if not p.exists():
                return
            p.with_suffix(p.suffix + ".ttl").write_text(str(ttl))

    async def ais_healthy(self) -> bool:
        try:
            tmp = self._dir / ".healthcheck"
            tmp.write_text("ok")
            tmp.unlink(missing_ok=True)
            return True
        except Exception:
            return False

    async def aclose(self) -> None:
        # Nothing to close
        return None


class CacheBackendFactory:
    """Factory for creating cache backend instances."""

    @staticmethod
    def create(
        config: MemoryCacheConfig | RedisCacheConfig | FileCacheConfig,
    ) -> BaseBackend:
        if isinstance(config, MemoryCacheConfig):
            return MemoryCacheBackend(config)
        if isinstance(config, RedisCacheConfig):
            return RedisCacheBackend(config)
        if isinstance(config, FileCacheConfig):
            return FileCacheBackend(config)
        raise CacheBackendError(
            message=f"Unsupported backend config: {type(config).__name__}",
            backend_name=getattr(config, "name", None),
        )
