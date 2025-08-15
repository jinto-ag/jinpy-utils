"""Tests for jinpy_utils.cache.config."""

import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from jinpy_utils.cache.config import (
    CacheManagerConfig,
    FileCacheConfig,
    MemoryCacheConfig,
    RedisCacheConfig,
)
from jinpy_utils.cache.enums import CacheBackendType


class TestBackendConfigs:
    def test_memory_defaults(self) -> None:
        cfg = MemoryCacheConfig(name="mem")
        assert cfg.backend_type == CacheBackendType.MEMORY
        assert cfg.thread_safe is True

    def test_file_creates_dir(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "cachedir"
            cfg = FileCacheConfig(name="file", directory=p)
            assert cfg.directory.exists()

    def test_redis_url_validator(self) -> None:
        _ = RedisCacheConfig(name="r1", url="redis://localhost:6379/0")
        with pytest.raises(ValueError):
            RedisCacheConfig(name="bad", url="http://not-redis")


class TestManagerConfig:
    def test_unique_names_validator(self) -> None:
        with pytest.raises(ValidationError):
            CacheManagerConfig(backends=[MemoryCacheConfig(name="x"), MemoryCacheConfig(name="x")])

    def test_default_backend_field(self) -> None:
        cfg = CacheManagerConfig(backends=[MemoryCacheConfig(name="m")], default_backend="m")
        assert cfg.default_backend == "m"
