from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping


class CacheInterface(ABC):
    """Abstract cache interface supporting sync operations."""

    @abstractmethod
    def get(self, key: str) -> Any | None: ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl: float | None = None) -> None: ...

    @abstractmethod
    def delete(self, key: str) -> None: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...

    @abstractmethod
    def clear(self) -> None: ...

    @abstractmethod
    def get_many(self, keys: list[str]) -> dict[str, Any | None]: ...

    @abstractmethod
    def set_many(self, items: Mapping[str, Any], ttl: float | None = None) -> None: ...

    @abstractmethod
    def delete_many(self, keys: list[str]) -> None: ...

    @abstractmethod
    def incr(self, key: str, amount: int = 1, ttl: float | None = None) -> int: ...

    @abstractmethod
    def decr(self, key: str, amount: int = 1, ttl: float | None = None) -> int: ...

    @abstractmethod
    def ttl(self, key: str) -> float | None: ...

    @abstractmethod
    def touch(self, key: str, ttl: float) -> None: ...

    @abstractmethod
    def is_healthy(self) -> bool: ...

    @abstractmethod
    def close(self) -> None: ...


class AsyncCacheInterface(ABC):
    """Abstract cache interface supporting async operations."""

    @abstractmethod
    async def aget(self, key: str) -> Any | None: ...

    @abstractmethod
    async def aset(self, key: str, value: Any, ttl: float | None = None) -> None: ...

    @abstractmethod
    async def adelete(self, key: str) -> None: ...

    @abstractmethod
    async def aexists(self, key: str) -> bool: ...

    @abstractmethod
    async def aclear(self) -> None: ...

    @abstractmethod
    async def aget_many(self, keys: list[str]) -> dict[str, Any | None]: ...

    @abstractmethod
    async def aset_many(
        self, items: Mapping[str, Any], ttl: float | None = None
    ) -> None: ...

    @abstractmethod
    async def adelete_many(self, keys: list[str]) -> None: ...

    @abstractmethod
    async def aincr(
        self, key: str, amount: int = 1, ttl: float | None = None
    ) -> int: ...

    @abstractmethod
    async def adecr(
        self, key: str, amount: int = 1, ttl: float | None = None
    ) -> int: ...

    @abstractmethod
    async def attl(self, key: str) -> float | None: ...

    @abstractmethod
    async def atouch(self, key: str, ttl: float) -> None: ...

    @abstractmethod
    async def ais_healthy(self) -> bool: ...

    @abstractmethod
    async def aclose(self) -> None: ...
