"""Shared paths/helpers for P006.7.11.7.18 Bundle 17N."""
from __future__ import annotations
from csv import DictReader
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SPATIAL_ROOT = ROOT / "data" / "novegeo" / "nngla" / "spatial-fabric" / "source"
CONTROL_ROOT = SPATIAL_ROOT / "02_controlled_codes"
FOUNDATION_AUTHORITY_MATRIX_PATH = ROOT / "data" / "novegeo" / "nngla" / "foundation" / "source" / "nexilabs_runtime_authority_matrix.csv"

COMMAND_CATALOGUE_PATH = CONTROL_ROOT / "novegeo_runtime_command_catalogue_v001.csv"
COMMAND_AUTHORIZATION_PATH = CONTROL_ROOT / "novegeo_runtime_command_authorization_matrix_v001.csv"
BULK_POLICY_PATH = CONTROL_ROOT / "novegeo_runtime_bulk_operation_policy_v001.csv"
IDEMPOTENCY_POLICY_PATH = CONTROL_ROOT / "novegeo_runtime_idempotency_policy_v001.csv"
VALIDATION_RULES_PATH = CONTROL_ROOT / "novegeo_runtime_command_validation_rules_v001.csv"
SCHEMA_PATH = ROOT / "database" / "schemas" / "nngla_runtime_command_services.sql"

def csv_rows(path: Path) -> tuple[dict[str, str], ...]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in DictReader(handle))

def bool_text(value: object) -> bool:
    return str(value).strip().lower() == "true"

def semantic_fingerprint(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    return sha256(encoded).hexdigest()

__all__ = [name for name in globals() if name.isupper() or name in {"csv_rows","bool_text","semantic_fingerprint"}]
