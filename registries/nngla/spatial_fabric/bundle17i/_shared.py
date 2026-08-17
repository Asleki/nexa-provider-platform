"""Bundle 17I title, tenure and state-land source paths and CSV helpers."""
from __future__ import annotations

from csv import DictReader
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CADASTRE_ROOT = ROOT / "data" / "novegeo" / "nngla" / "cadastre-titles-state-land" / "source"
CONTROLLED_ROOT = CADASTRE_ROOT / "02_controlled_codes"
LAND_ROOT = CADASTRE_ROOT / "07_land"
DAY_ZERO_TITLE_PATH = LAND_ROOT / "title_bootstrap.csv"
DAY_ZERO_STATE_LAND_PATH = LAND_ROOT / "state_land_bootstrap.csv"
TITLE_TYPES_PATH = CONTROLLED_ROOT / "title_types.csv"
TENURE_TYPES_PATH = CONTROLLED_ROOT / "tenure_types.csv"
STATE_LAND_CATEGORIES_PATH = CONTROLLED_ROOT / "state_land_categories.csv"


def csv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in DictReader(handle))


def csv_header(path: Path) -> tuple[str, ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = DictReader(handle)
        return tuple(reader.fieldnames or ())


def stable_id(prefix: str, *parts: str) -> str:
    payload = "\x1f".join(str(part) for part in parts).encode("utf-8")
    return f"{prefix}{sha256(payload).hexdigest()}"


__all__ = [
    "ROOT", "CADASTRE_ROOT", "CONTROLLED_ROOT", "LAND_ROOT", "DAY_ZERO_TITLE_PATH", "DAY_ZERO_STATE_LAND_PATH",
    "TITLE_TYPES_PATH", "TENURE_TYPES_PATH", "STATE_LAND_CATEGORIES_PATH", "csv_rows", "csv_header", "stable_id",
]
