from __future__ import annotations

import json
import pickle
import time
from collections.abc import Callable
from typing import Any, Literal

SerializerType = Literal["json", "pickle", "str", "bytes"]


def normalize_key(key: str) -> str:
    """Normalize cache key to a safe form."""
    key = key.strip()
    if not key:
        raise ValueError("Cache key cannot be empty")
    # Prevent accidental whitespace/control characters
    return "".join(ch for ch in key if ch.isprintable())


def now_seconds() -> float:
    """Current monotonic-ish epoch seconds."""
    return time.time()


def compute_expiry(ttl: float | None) -> float | None:
    """Compute absolute expiry timestamp in seconds."""
    if ttl is None:
        return None
    if ttl <= 0:
        # Immediate expiry
        return now_seconds() - 1
    return now_seconds() + ttl


def remaining_ttl(expiry: float | None) -> float | None:
    """Compute remaining ttl from absolute expiry."""
    if expiry is None:
        return None
    remaining = expiry - now_seconds()
    return remaining if remaining > 0 else 0.0


def default_serializer(
    kind: SerializerType,
) -> tuple[Callable[[Any], bytes], Callable[[bytes], Any]]:
    """Return serializer, deserializer functions based on kind."""
    if kind == "json":

        def ser(obj: Any) -> bytes:
            return json.dumps(
                obj, default=str, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")

        def de(data: bytes) -> Any:
            return json.loads(data.decode("utf-8"))

        return ser, de

    if kind == "pickle":

        def ser(obj: Any) -> bytes:
            return pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)

        def de(data: bytes) -> Any:
            return pickle.loads(data)

        return ser, de

    if kind == "str":

        def ser(obj: Any) -> bytes:
            return str(obj).encode("utf-8")

        def de(data: bytes) -> Any:
            return data.decode("utf-8")

        return ser, de

    if kind == "bytes":

        def ser(obj: Any) -> bytes:
            if isinstance(obj, (bytes, bytearray, memoryview)):
                return bytes(obj)
            raise TypeError("Expected bytes-like value")

        def de(data: bytes) -> Any:
            return data

        return ser, de

    raise ValueError(f"Unsupported serializer type: {kind}")
