"""Exact-byte SHA-256 checksum services for immutable migration artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from collections.abc import Iterable

from .errors import MigrationChecksumError


def sha256_bytes(value: bytes) -> str:
    if not isinstance(value, bytes):
        raise TypeError("sha256_bytes requires bytes.")
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def verify_checksum(path: str | Path, expected_sha256: str) -> str:
    actual = sha256_file(path)
    expected = expected_sha256.lower()
    if actual != expected:
        raise MigrationChecksumError(
            f"checksum mismatch for {Path(path).name}: expected {expected}, got {actual}."
        )
    return actual


def canonical_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256_bytes(payload)


def ordered_plan_digest(rows: Iterable[dict[str, object]]) -> str:
    return canonical_digest(list(rows))


__all__ = ["sha256_bytes", "sha256_file", "verify_checksum", "canonical_digest", "ordered_plan_digest"]
