"""Bundle 17C deterministic helpers."""
from __future__ import annotations

import csv
from hashlib import sha256
from pathlib import Path

from registries.nngla.spatial_fabric.source_inventory import ROOT, SOURCE_ROOT


def csv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def stable_id(prefix: str, *parts: str) -> str:
    payload = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}{sha256(payload).hexdigest()}"


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


__all__ = ["ROOT", "SOURCE_ROOT", "csv_rows", "stable_id", "file_sha256"]
