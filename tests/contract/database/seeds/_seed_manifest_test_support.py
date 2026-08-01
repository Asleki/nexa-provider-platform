from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

SEED_ROOT = Path("database/seeds")


def load_manifest(relative_path: str) -> dict[str, Any]:
    path = SEED_ROOT / relative_path
    return json.loads(path.read_text(encoding="utf-8"))


def file_rows(file_entry: dict[str, Any]) -> tuple[list[str], list[dict[str, str]]]:
    path = SEED_ROOT / file_entry["path"]
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames is not None
        return list(reader.fieldnames), list(reader)


def assert_common_manifest_contract(manifest: dict[str, Any]) -> None:
    assert manifest["manifest_schema"] == "npp.production-seed-manifest"
    assert manifest["manifest_schema_version"] == 1
    assert manifest["classification"] == "production_seed"
    assert manifest["status"] == "approved"
    assert manifest["encoding"] == "utf-8"
    assert manifest["delimiter"] == ","
    assert manifest["normalization"] == {
        "owner": "python",
        "canonical_unicode_form": "NFC",
        "comparison_unicode_form": "NFKC",
        "comparison_case_strategy": "casefold",
        "database_generates_search_value": False,
        "accent_stripping_authorized": False,
    }
    runtime = manifest["runtime_policy"]
    assert runtime["dataset_is_runtime_neutral"] is True
    assert runtime["eligible_runtime_modes"] == ["simulation", "production"]
    assert runtime["single_runtime_per_import_batch"] is True
    assert runtime["automatic_cross_runtime_copy"] is False
    governance = manifest["governance"]
    assert governance["direct_sql_import_allowed"] is False
    assert governance["postgresql_copy_allowed"] is False
    assert governance["source_ids_are_canonical_ids"] is False
    assert governance["python_validation_required"] is True
    assert governance["manifest_integrity_verification_required"] is True


def assert_file_integrity(file_entry: dict[str, Any]) -> list[dict[str, str]]:
    path = SEED_ROOT / file_entry["path"]
    assert path.is_file(), path
    payload = path.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == file_entry["sha256"]
    headers, rows = file_rows(file_entry)
    assert headers == file_entry["required_headers"]
    assert len(rows) == file_entry["row_count"]
    assert rows
    id_header = next(header for header in headers if header.lower() == "id")
    source_ids = [row[id_header].strip() for row in rows]
    assert all(source_ids)
    assert len(source_ids) == len(set(source_ids))
    return rows
