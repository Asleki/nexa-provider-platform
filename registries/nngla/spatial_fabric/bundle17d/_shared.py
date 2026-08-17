"""Bundle 17D deterministic marine-source helpers."""
from __future__ import annotations

import csv
from hashlib import sha256
from pathlib import Path

from registries.nngla.spatial_fabric.source_inventory import ROOT, SOURCE_ROOT

MARINE_ROOT = SOURCE_ROOT / "05_new_waters_ocean"


def csv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def source_reference_matches(row: dict[str, str]) -> bool:
    source_path = row.get("source_path_reference") or row.get("boundary_source_reference") or ""
    expected = row.get("source_sha256", "")
    if not source_path:
        return True
    path = ROOT / source_path
    if not path.is_file():
        return False
    return not expected or file_sha256(path) == expected


__all__ = ["ROOT", "SOURCE_ROOT", "MARINE_ROOT", "csv_rows", "file_sha256", "source_reference_matches"]
