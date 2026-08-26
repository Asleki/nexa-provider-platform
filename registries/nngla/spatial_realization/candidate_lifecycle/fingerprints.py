"""Deterministic hashing helpers for Delivery-2 candidate lifecycle records."""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from hashlib import sha256
import json


def _normalize(value):
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (tuple, list)):
        return [_normalize(v) for v in value]
    return value


def canonical_json(value) -> str:
    return json.dumps(_normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def stable_id(prefix: str, value) -> str:
    return prefix + digest(value)


__all__ = ["canonical_json", "digest", "stable_id"]
