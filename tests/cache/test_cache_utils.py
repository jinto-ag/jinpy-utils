"""Tests for jinpy_utils.cache.utils."""

import time

import pytest

from jinpy_utils.cache.utils import (
    compute_expiry,
    default_serializer,
    normalize_key,
    now_seconds,
    remaining_ttl,
)


class TestNormalizeKey:
    def test_normalize_key_basic(self) -> None:
        assert normalize_key("  key \t ") == "key"
        assert normalize_key("a\n\tb\u200b") == "ab"

    def test_normalize_key_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            normalize_key("   ")


class TestExpiry:
    def test_compute_expiry_none_zero_negative_and_remaining(self) -> None:
        assert compute_expiry(None) is None
        assert remaining_ttl(compute_expiry(0)) == 0.0
        assert remaining_ttl(compute_expiry(-5)) == 0.0
        ex = compute_expiry(0.05)
        assert ex is not None
        assert remaining_ttl(ex) is None or remaining_ttl(ex) >= 0


class TestDefaultSerializer:
    def test_json_serializer(self) -> None:
        ser, de = default_serializer("json")
        data = {"a": 1, "b": "x"}
        raw = ser(data)
        assert de(raw) == data

    def test_pickle_serializer(self) -> None:
        ser, de = default_serializer("pickle")
        obj = {"x": [1, 2, 3], "y": (4, 5)}
        raw = ser(obj)
        assert de(raw) == obj

    def test_str_serializer(self) -> None:
        ser, de = default_serializer("str")
        raw = ser(123)
        assert raw == b"123"
        assert de(raw) == "123"

    def test_bytes_serializer(self) -> None:
        ser, de = default_serializer("bytes")
        raw = ser(b"abc")
        assert raw == b"abc"
        assert de(raw) == b"abc"
        with pytest.raises(TypeError):
            ser("not-bytes")  # type: ignore[arg-type]

    def test_unsupported_serializer_raises(self) -> None:
        with pytest.raises(ValueError):
            default_serializer("unknown")  # type: ignore[arg-type]


def test_now_seconds_returns_float() -> None:
    t = now_seconds()
    assert isinstance(t, float)


def test_remaining_ttl_none_input_is_none() -> None:
    # Explicitly cover remaining_ttl(None) branch
    assert remaining_ttl(None) is None
