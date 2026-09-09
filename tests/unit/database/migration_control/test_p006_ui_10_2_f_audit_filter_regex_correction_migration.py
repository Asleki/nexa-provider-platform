from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


CORRECTION_ID = "m006_10_02_enrollment_notification_audit_filter_regex_correction"
CORRECTION_SEQUENCE = 36
CORRECTION_DEPENDENCY = "m006_10_02_enrollment_notification_audit_persistence"

FORWARD = f"{CORRECTION_ID}.sql"
ROLLBACK = f"{CORRECTION_ID}_rollback.sql"

SEQUENCE_35_FORWARD_SHA256 = (
    "9521c7a30a4c20c64b2949368ac44e6177bc01a49afd2e12af715ab8436433b1"
)

CONSTRAINT = "ck_nexilabs_auth_audit_export_filter_reference"

CORRECTED_PATTERN = (
    "^[A-Z][A-Z0-9_]{2,79}:"
    "[A-Za-z0-9][A-Za-z0-9._:/=-]*$"
)

SEQUENCE_35_PATTERN = (
    "^[A-Z][A-Z0-9_]{2,79}:"
    "[A-Za-z0-9][A-Za-z0-9._:/=-]{0,1966}$"
)


def root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "database/migrations" / FORWARD).is_file():
            return candidate
    raise AssertionError("repository root not found")


def test_sequence_36_replaces_only_the_broken_filter_constraint() -> None:
    sql = (root() / "database/migrations" / FORWARD).read_text()

    assert sql.startswith("BEGIN;\n")
    assert sql.rstrip().endswith("COMMIT;")

    assert f"DROP CONSTRAINT {CONSTRAINT};" in sql
    assert f"ADD CONSTRAINT {CONSTRAINT} CHECK (" in sql

    assert CORRECTED_PATTERN in sql
    assert SEQUENCE_35_PATTERN not in sql

    assert "INSERT INTO" not in sql.upper()
    assert "DROP TABLE" not in sql.upper()
    assert "CREATE TABLE" not in sql.upper()


def test_sequence_36_rollback_restores_exact_sequence_35_expression() -> None:
    rollback = (root() / "database/migrations" / ROLLBACK).read_text()

    assert rollback.startswith("BEGIN;\n")
    assert rollback.rstrip().endswith("COMMIT;")
    assert "disposable/safe qualification targets only" in rollback

    assert f"DROP CONSTRAINT {CONSTRAINT};" in rollback
    assert f"ADD CONSTRAINT {CONSTRAINT} CHECK (" in rollback
    assert SEQUENCE_35_PATTERN in rollback


def test_manifest_sequence_36_is_exact_and_sequence_35_remains_immutable() -> None:
    repo = root()

    manifest = json.loads(
        (repo / "database/migrations/migration_manifest.json").read_text()
    )

    assert manifest["catalogue_version"] >= 20
    assert len(manifest["migrations"]) >= 36
    assert [
        row["sequence_number"] for row in manifest["migrations"][:36]
    ] == list(range(1, 37))

    row35 = manifest["migrations"][34]
    row36 = manifest["migrations"][35]

    original_35 = (
        repo
        / "database/migrations/m006_10_02_enrollment_notification_audit_persistence.sql"
    ).read_bytes()

    assert row35["forward_sha256"] == SEQUENCE_35_FORWARD_SHA256
    assert sha256(original_35).hexdigest() == SEQUENCE_35_FORWARD_SHA256

    assert row36["migration_id"] == CORRECTION_ID
    assert row36["milestone_id"] == "M006.10.2"
    assert row36["sequence_number"] == CORRECTION_SEQUENCE
    assert row36["depends_on"] == [CORRECTION_DEPENDENCY]

    assert row36["expected_objects"]["tables"] == [
        "nexilabs_auth.audit_export"
    ]
    assert row36["expected_objects"]["constraints"] == [
        "nexilabs_auth.ck_nexilabs_auth_audit_export_filter_reference"
    ]

    for filename, hash_key, size_key in (
        (FORWARD, "forward_sha256", "forward_byte_size"),
        (ROLLBACK, "rollback_sha256", "rollback_byte_size"),
    ):
        raw = (repo / "database/migrations" / filename).read_bytes()
        assert row36[hash_key] == sha256(raw).hexdigest()
        assert row36[size_key] == len(raw)
