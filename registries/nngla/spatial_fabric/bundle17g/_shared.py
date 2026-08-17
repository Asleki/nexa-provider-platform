"""Bundle 17G cadastre source paths and CSV helpers."""
from __future__ import annotations
from csv import DictReader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CADASTRE_ROOT = ROOT / "data" / "novegeo" / "nngla" / "cadastre-titles-state-land" / "source"
CONTROLLED_ROOT = CADASTRE_ROOT / "02_controlled_codes"
LAND_ROOT = CADASTRE_ROOT / "07_land"
DAY_ZERO_PARCEL_PATH = LAND_ROOT / "parcel_bootstrap.csv"
LAND_USE_PATH = CONTROLLED_ROOT / "land_use_codes.csv"


def csv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in DictReader(handle))


def csv_header(path: Path) -> tuple[str, ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = DictReader(handle)
        return tuple(reader.fieldnames or ())


__all__ = ["ROOT", "CADASTRE_ROOT", "CONTROLLED_ROOT", "LAND_ROOT", "DAY_ZERO_PARCEL_PATH", "LAND_USE_PATH", "csv_rows", "csv_header"]
