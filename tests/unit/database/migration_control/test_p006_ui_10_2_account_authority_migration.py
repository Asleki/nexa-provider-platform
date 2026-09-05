from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

from database.migration_control.manifest import MigrationManifestLoader
from database.migration_control.naming import parse_migration_filename


MIGRATION_ID = "m006_10_02_nexilabs_account_credential_authority"
MILESTONE_ID = "M006.10.2"
FORWARD = f"{MIGRATION_ID}.sql"
ROLLBACK = f"{MIGRATION_ID}_rollback.sql"
EXPECTED_TABLES = {
    "nexilabs_auth.principal_account",
    "nexilabs_auth.principal_profile",
    "nexilabs_auth.principal_permission",
    "nexilabs_auth.account_email",
    "nexilabs_auth.credential_verifier",
    "nexilabs_auth.developer_access_request",
    "nexilabs_auth.developer_setup",
    "nexilabs_auth.enigma_catalogue",
    "nexilabs_auth.enigma_catalogue_entry",
    "nexilabs_auth.enigma_profile",
    "nexilabs_auth.enigma_profile_catalogue",
    "nexilabs_auth.principal_enigma_profile",
}
EXPECTED_INDEXES = {
    "ux_nexilabs_auth_principal_username_key",
    "ix_nexilabs_auth_principal_identity_state",
    "ux_nexilabs_auth_active_permission",
    "ix_nexilabs_auth_permission_principal",
    "ux_nexilabs_auth_email_key",
    "ux_nexilabs_auth_primary_email",
    "ix_nexilabs_auth_email_principal_state",
    "ux_nexilabs_auth_active_password",
    "ix_nexilabs_auth_credential_principal_state",
    "ux_nexilabs_auth_open_developer_request_email",
    "ix_nexilabs_auth_developer_request_state",
    "ux_nexilabs_auth_developer_setup_lookup_key",
    "ux_nexilabs_auth_active_developer_setup_request",
    "ux_nexilabs_auth_developer_setup_result_principal",
    "ix_nexilabs_auth_developer_setup_state_expiry",
    "ux_nexilabs_auth_enigma_catalogue_version",
    "ux_nexilabs_auth_active_enigma_catalogue",
    "ix_nexilabs_auth_enigma_catalogue_entry_lookup",
    "ix_nexilabs_auth_enigma_profile_state",
    "ix_nexilabs_auth_enigma_profile_catalogue",
    "ux_nexilabs_auth_active_principal_enigma_profile",
    "ux_nexilabs_auth_active_profile_assignment",
}


def _root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "database" / "migrations" / "migration_manifest.json").is_file():
            return candidate
    raise AssertionError("repository root not found")


def test_migration_filename_is_accepted_by_the_real_npp_parser() -> None:
    forward = parse_migration_filename(FORWARD)
    rollback = parse_migration_filename(ROLLBACK)
    assert forward.migration_id == MIGRATION_ID
    assert forward.milestone_id == MILESTONE_ID
    assert forward.direction == "forward"
    assert rollback.migration_id == MIGRATION_ID
    assert rollback.milestone_id == MILESTONE_ID
    assert rollback.direction == "rollback"


def test_forward_migration_creates_governed_empty_authority_only() -> None:
    sql = (_root() / "database" / "migrations" / FORWARD).read_text(encoding="utf-8")
    assert sql.startswith("BEGIN;\n")
    assert sql.rstrip().endswith("COMMIT;")
    assert "CREATE SCHEMA IF NOT EXISTS nexilabs_auth;" in sql
    assert "REVOKE ALL ON SCHEMA nexilabs_auth FROM PUBLIC;" in sql
    assert "REVOKE ALL ON ALL TABLES IN SCHEMA nexilabs_auth FROM PUBLIC;" in sql

    tables = set(re.findall(r"CREATE TABLE\s+([a-z0-9_.]+)\s*\(", sql, re.IGNORECASE))
    indexes = set(
        re.findall(
            r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+([a-z0-9_]+)",
            sql,
            re.IGNORECASE,
        )
    )
    assert tables == EXPECTED_TABLES
    assert indexes == EXPECTED_INDEXES
    assert not re.search(r"\bINSERT\s+INTO\b", sql, re.IGNORECASE)
    assert "ON DELETE CASCADE" not in sql.upper()


def test_persistence_schema_preserves_existing_identity_and_runtime_semantics() -> None:
    sql = (_root() / "database" / "migrations" / FORWARD).read_text(encoding="utf-8")
    assert "identity_type IN ('guest', 'nexadevs_developer')" in sql
    assert "CREATE TABLE nexilabs_auth.principal_role" not in sql
    assert "runtime_scope" not in sql
    assert "verification_reference text NULL" in sql
    assert "simulation_user" not in sql
    assert "production_user" not in sql


def test_credentials_setup_and_enigma_do_not_persist_plaintext_secret_material() -> None:
    sql = (_root() / "database" / "migrations" / FORWARD).read_text(encoding="utf-8")
    lower = sql.lower()
    assert "verifier_scheme" in lower
    assert "verifier_payload" in lower
    assert "setup_lookup_key" in lower
    assert "setup_secret_verifier_scheme" in lower
    assert "setup_secret_verifier_payload" in lower
    assert "profile_lookup_word" not in lower
    assert "profile_lookup_token" not in lower
    assert "password_plaintext" not in lower
    assert "raw_password" not in lower
    assert "setup_secret_plaintext" not in lower
    assert "Public/non-secret setup locator" not in sql
    assert "archive_password" not in lower

    # Qualify against structural development-fixture markers without embedding
    # any private fixture credential values in this test artifact.
    assert not re.search(r"\b(?:guest|developer)_demo\b", lower)
    assert not re.search(r"(?:guest|developer):[^\s']*development", lower)
    assert not re.search(r"enigma-profile:[^\s']*development", lower)


def test_enigma_catalogue_profile_relationship_is_foundational_not_final_secret_design() -> None:
    sql = (_root() / "database" / "migrations" / FORWARD).read_text(encoding="utf-8")
    for table in (
        "enigma_catalogue",
        "enigma_catalogue_entry",
        "enigma_profile",
        "enigma_profile_catalogue",
        "principal_enigma_profile",
    ):
        assert f"CREATE TABLE nexilabs_auth.{table} (" in sql
    assert "Secret lookup/response material is intentionally not modeled" in sql


def test_rollback_is_explicit_reverse_order_without_cascade() -> None:
    sql = (_root() / "database" / "migrations" / ROLLBACK).read_text(encoding="utf-8")
    assert sql.startswith("BEGIN;\n")
    assert sql.rstrip().endswith("COMMIT;")
    assert "CASCADE" not in sql.upper()
    dropped = re.findall(
        r"DROP TABLE IF EXISTS\s+([a-z0-9_.]+);",
        sql,
        flags=re.IGNORECASE,
    )
    assert dropped == [
        "nexilabs_auth.principal_enigma_profile",
        "nexilabs_auth.enigma_profile_catalogue",
        "nexilabs_auth.enigma_profile",
        "nexilabs_auth.enigma_catalogue_entry",
        "nexilabs_auth.enigma_catalogue",
        "nexilabs_auth.developer_setup",
        "nexilabs_auth.developer_access_request",
        "nexilabs_auth.credential_verifier",
        "nexilabs_auth.account_email",
        "nexilabs_auth.principal_permission",
        "nexilabs_auth.principal_profile",
        "nexilabs_auth.principal_account",
    ]
    assert "DROP SCHEMA IF EXISTS nexilabs_auth;" in sql


def test_manifest_tail_is_sequence_31_and_artifact_integrity_is_exact() -> None:
    root = _root()
    manifest_path = root / "database" / "migrations" / "migration_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["catalogue_version"] == 15
    row = manifest["migrations"][-1]
    assert row["migration_id"] == MIGRATION_ID
    assert row["milestone_id"] == MILESTONE_ID
    assert row["sequence_number"] == 31
    assert row["depends_on"] == [
        "m006_07_11_nngla_municipality_public_read_qualification_admission_correction"
    ]
    assert set(row["expected_objects"]["schemas"]) == {"nexilabs_auth"}
    assert set(row["expected_objects"]["tables"]) == EXPECTED_TABLES
    assert set(row["expected_objects"]["indexes"]) == EXPECTED_INDEXES
    assert row["expected_objects"]["constraints"] == []
    assert row["expected_objects"]["views"] == []
    assert row["expected_objects"]["functions"] == []
    assert row["transaction_policy"] == "embedded"
    assert row["destructive"] is False

    for filename, hash_key, size_key in (
        (FORWARD, "forward_sha256", "forward_byte_size"),
        (ROLLBACK, "rollback_sha256", "rollback_byte_size"),
    ):
        path = root / "database" / "migrations" / filename
        assert row[hash_key] == sha256(path.read_bytes()).hexdigest()
        assert row[size_key] == path.stat().st_size

    catalogue = MigrationManifestLoader().load(manifest_path)
    assert catalogue.definitions[-1].identity.migration_id == MIGRATION_ID
    assert catalogue.definitions[-1].identity.milestone_id == MILESTONE_ID
