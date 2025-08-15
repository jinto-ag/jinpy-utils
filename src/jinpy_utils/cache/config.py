from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import CacheBackendType


class BaseCacheBackendConfig(BaseModel):
    """Base configuration for all cache backends."""

    backend_type: CacheBackendType
    name: str = Field(..., description="Unique backend name")
    enabled: bool = True
    default_ttl: float | None = Field(
        default=None, ge=0, description="Default TTL in seconds"
    )
    serializer: Literal["json", "pickle", "str", "bytes"] = "json"

    model_config = ConfigDict(extra="allow", use_enum_values=True)


class MemoryCacheConfig(BaseCacheBackendConfig):
    """Configuration for in-memory cache."""

    backend_type: CacheBackendType = CacheBackendType.MEMORY
    max_entries: int | None = Field(
        default=None,
        ge=1,
        description="Optional max entries for eviction (FIFO)",
    )
    thread_safe: bool = True


class RedisCacheConfig(BaseCacheBackendConfig):
    """Configuration for Redis cache (async)."""

    backend_type: CacheBackendType = CacheBackendType.REDIS
    url: str = Field(
        ...,
        description="Redis URL, e.g., redis://localhost:6379/0",
    )
    decode_responses: bool = False
    pool_size: int = Field(default=10, ge=1, le=100)
    connect_timeout: float = Field(default=5.0, gt=0)
    command_timeout: float = Field(default=2.0, gt=0)
    ssl: bool = False

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("redis://", "rediss://")):
            raise ValueError("Redis URL must start with redis:// or rediss://")
        return v


class FileCacheConfig(BaseCacheBackendConfig):
    """Configuration for file-based cache."""

    backend_type: CacheBackendType = CacheBackendType.FILE
    directory: Path = Field(
        default=Path(".cache"),
        description="Directory for stored cache entries",
    )
    file_extension: str = Field(default=".bin")
    max_entries: int | None = Field(default=None, ge=1)

    @field_validator("directory")
    @classmethod
    def ensure_dir(cls, v: Path) -> Path:
        v.mkdir(parents=True, exist_ok=True)
        return v


class CacheManagerConfig(BaseModel):
    """Global cache manager configuration."""

    backends: list[MemoryCacheConfig | RedisCacheConfig | FileCacheConfig] = Field(
        default_factory=list
    )
    enable_singleton: bool = Field(default=True)
    async_queue_size: int = Field(default=10_000, gt=0)
    default_backend: str | None = Field(
        default=None, description="Default backend name to use"
    )

    model_config = ConfigDict(use_enum_values=True, extra="ignore")

    @field_validator("backends")
    @classmethod
    def validate_backends(cls, v: list[Any]) -> list[Any]:
        names = [b.name for b in v if hasattr(b, "name")]
        if len(names) != len(set(names)):
            raise ValueError("Backend names must be unique")
        return v
