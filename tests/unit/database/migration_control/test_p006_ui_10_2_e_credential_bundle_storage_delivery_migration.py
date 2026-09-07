from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re


E_MIGRATION_ID = "m006_10_02_credential_bundle_storage_delivery"
E_FORWARD_FILE = f"{E_MIGRATION_ID}.sql"
E_ROLLBACK_FILE = f"{E_MIGRATION_ID}_rollback.sql"
E_SEQUENCE = 34
E_DEPENDENCY = "m006_10_02_email_verification_challenge"

REQUIRED_E_TABLES = {
    "nexilabs_auth.credential_bundle",
    "nexilabs_auth.credential_bundle_secret",
    "nexilabs_auth.credential_delivery",
}
REQUIRED_E_INDEXES = {
    "ux_nexilabs_auth_current_credential_bundle",
    "ux_nexilabs_auth_credential_bundle_object",
    "ix_nexilabs_auth_credential_bundle_principal",
    "ix_nexilabs_auth_credential_bundle_state_expiry",
    "ux_nexilabs_auth_active_credential_bundle_secret",
    "ix_nexilabs_auth_credential_bundle_secret_bundle",
    "ux_nexilabs_auth_issued_credential_delivery",
    "ix_nexilabs_auth_credential_delivery_bundle",
    "ix_nexilabs_auth_credential_delivery_state_expiry",
}
REQUIRED_E_FUNCTIONS = {
    "validate_credential_bundle_owner",
    "validate_credential_bundle_transition",
    "validate_credential_bundle_secret_transition",
    "validate_credential_delivery_transition",
    "validate_credential_delivery_bundle",
}

REQUIRED_E_CONSTRAINTS = {
    "fk_nexilabs_auth_credential_bundle_principal",
    "fk_nexilabs_auth_credential_bundle_enigma_profile",
    "ck_nexilabs_auth_credential_bundle_id_nonblank",
    "ck_nexilabs_auth_credential_bundle_object_provider",
    "ck_nexilabs_auth_credential_bundle_object_key",
    "ck_nexilabs_auth_credential_bundle_sha256",
    "ck_nexilabs_auth_credential_bundle_byte_size",
    "ck_nexilabs_auth_credential_bundle_state",
    "ck_nexilabs_auth_credential_bundle_expiry_retention",
    "ck_nexilabs_auth_credential_bundle_ready_evidence",
    "ck_nexilabs_auth_credential_bundle_invalidation_time",
    "ck_nexilabs_auth_credential_bundle_retired_time",
    "fk_nexilabs_auth_credential_bundle_secret_bundle",
    "ck_nexilabs_auth_credential_bundle_secret_id_nonblank",
    "ck_nexilabs_auth_credential_bundle_secret_provider",
    "ck_nexilabs_auth_credential_bundle_secret_reference",
    "ck_nexilabs_auth_credential_bundle_secret_context",
    "ck_nexilabs_auth_credential_bundle_secret_retirement",
    "fk_nexilabs_auth_credential_delivery_bundle",
    "ck_nexilabs_auth_credential_delivery_id_nonblank",
    "ck_nexilabs_auth_delivery_verifier_scheme",
    "ck_nexilabs_auth_delivery_verifier_version",
    "ck_nexilabs_auth_delivery_verifier_payload",
    "ck_nexilabs_auth_credential_delivery_state",
    "ck_nexilabs_auth_credential_delivery_policy",
    "ck_nexilabs_auth_credential_delivery_host",
    "ck_nexilabs_auth_credential_delivery_expiry",
    "ck_nexilabs_auth_credential_delivery_state_timestamps",
    "ck_nexilabs_auth_credential_delivery_consumed_time",
    "ck_nexilabs_auth_credential_delivery_revoked_time",
    "ck_nexilabs_auth_credential_delivery_download_accounting",
}
REQUIRED_E_TRIGGERS = {
    "tr_nexilabs_auth_credential_bundle_owner",
    "tr_nexilabs_auth_credential_bundle_transition",
    "tr_nexilabs_auth_credential_bundle_secret_transition",
    "tr_nexilabs_auth_credential_delivery_transition",
    "tr_nexilabs_auth_credential_delivery_bundle",
}


def _root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "database/migrations" / E_FORWARD_FILE).is_file():
            return candidate
    raise AssertionError("repository root not found")


def _sql() -> str:
    return (_root() / "database/migrations" / E_FORWARD_FILE).read_text(encoding="utf-8")


def test_e_forward_is_additive_zero_seed_and_three_table_only() -> None:
    sql = _sql()
    assert sql.startswith("BEGIN;\n") and sql.rstrip().endswith("COMMIT;")
    tables = set(re.findall(r"CREATE TABLE\s+([a-z0-9_.]+)\s*\(", sql, re.I))
    assert tables == REQUIRED_E_TABLES
    assert not re.search(r"\bINSERT\s+INTO\b", sql, re.I)
    assert "CREATE SCHEMA" not in sql.upper()
    for table in REQUIRED_E_TABLES:
        assert f"REVOKE ALL ON TABLE {table} FROM PUBLIC;" in sql


def test_bundle_is_nexadevs_same_owner_active_profile_bound_without_active_account_requirement() -> None:
    sql = _sql()
    assert "REFERENCES nexilabs_auth.principal_account(principal_id)" in sql
    assert "REFERENCES nexilabs_auth.enigma_profile(profile_id)" in sql
    assert "identity_value IS DISTINCT FROM 'nexadevs_developer'" in sql
    assert "profile_state_value IS DISTINCT FROM 'ACTIVE'" in sql
    assert "principal_enigma_profile" in sql
    assert "principal_id = NEW.principal_id" in sql
    assert "profile_id = NEW.enigma_profile_id" in sql
    assert "assignment_state = 'ACTIVE'" in sql
    assert "account_state = 'ACTIVE'" not in sql


def test_bundle_integrity_private_object_ready_and_retention_contract_is_structural() -> None:
    sql = _sql()
    assert "content_sha256 ~ '^[0-9a-f]{64}$'" in sql
    assert "byte_size > 0" in sql
    assert "retention_until >= expires_at" in sql
    assert "integrity_verified_at IS NOT NULL" in sql
    assert "object_confirmed_at IS NOT NULL" in sql
    assert "integrity_verified_at >= created_at" in sql
    assert "object_confirmed_at >= created_at" in sql
    assert "bundle_state <> 'GENERATED' OR ready_at IS NULL" in sql
    assert "ready_at >= integrity_verified_at" in sql
    assert "ready_at >= object_confirmed_at" in sql
    assert "ready_at <= expires_at" in sql
    assert "bundle_state <> 'READY'" in sql
    assert "object_key !~ '^[a-zA-Z][a-zA-Z0-9+.-]*://'" in sql
    assert "public, presigned or user-facing URL" in sql
    assert "BYTEA" not in sql.upper()


def test_optional_secret_authority_exposes_no_plaintext_password_column() -> None:
    sql = _sql()
    create = re.search(
        r"CREATE TABLE nexilabs_auth\.credential_bundle_secret\s*\((.*?)\n\);",
        sql,
        re.S,
    )
    assert create is not None
    table_sql = create.group(1).lower()
    assert "archive_password" not in table_sql
    assert "plaintext_password" not in table_sql
    assert "encrypted_secret_reference" in table_sql
    assert "encryption_context_version" in table_sql
    assert "plaintext:%" in sql.lower()
    assert "cleartext:%" in sql.lower()
    assert "never the plaintext archive password" in sql


def test_delivery_stores_verifier_not_raw_token_or_url_and_has_one_current_issuance() -> None:
    sql = _sql()
    create = re.search(
        r"CREATE TABLE nexilabs_auth\.credential_delivery\s*\((.*?)\n\);",
        sql,
        re.S,
    )
    assert create is not None
    table_sql = create.group(1).lower()
    assert "raw_token" not in table_sql
    assert "public_url" not in table_sql
    assert "presigned_url" not in table_sql
    assert "token_verifier_scheme" in table_sql
    assert "token_verifier_version" in table_sql
    assert "token_verifier_payload" in table_sql
    assert "logical_delivery_host_code ~ '^[A-Z][A-Z0-9_]{2,79}$'" in sql
    assert "WHERE delivery_state = 'ISSUED'" in sql
    assert "never the raw delivery token" in sql


def test_delivery_requires_ready_bundle_and_terminal_bundle_requires_delivery_closure() -> None:
    sql = _sql()
    assert "bundle_state_value IS DISTINCT FROM 'READY'" in sql
    assert "credential delivery requires a READY credential bundle" in sql
    assert "tr_nexilabs_auth_credential_delivery_bundle" in sql
    assert "delivery_state = 'ISSUED'" in sql
    assert "credential bundle cannot become terminal while a delivery remains ISSUED" in sql


def test_delivery_download_accounting_and_terminal_history_are_durable() -> None:
    sql = _sql()
    for state in ("ISSUED", "CONSUMED", "EXPIRED", "REVOKED"):
        assert f"'{state}'" in sql
    assert "download_count >= 0" in sql
    assert "first_downloaded_at IS NULL" in sql
    assert "first_downloaded_at <= last_downloaded_at" in sql
    assert "last_downloaded_at <= expires_at" in sql
    assert "download counter cannot decrease" in sql
    assert "terminal credential deliveries are immutable" in sql
    assert "credential deliveries are durable authority and cannot be deleted" in sql


def test_required_indexes_functions_and_narrow_rollback_are_present() -> None:
    sql = _sql()
    indexes = set(re.findall(r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+([a-z0-9_]+)", sql, re.I))
    functions = set(re.findall(r"CREATE FUNCTION\s+nexilabs_auth\.([a-z0-9_]+)", sql, re.I))
    constraints = set(re.findall(r"CONSTRAINT\s+([a-z0-9_]+)", sql, re.I))
    triggers = set(re.findall(r"CREATE TRIGGER\s+([a-z0-9_]+)", sql, re.I))
    assert indexes == REQUIRED_E_INDEXES
    assert functions == REQUIRED_E_FUNCTIONS
    assert constraints == REQUIRED_E_CONSTRAINTS
    assert triggers == REQUIRED_E_TRIGGERS
    rollback = (_root() / "database/migrations" / E_ROLLBACK_FILE).read_text(encoding="utf-8")
    assert rollback.startswith("BEGIN;\n") and rollback.rstrip().endswith("COMMIT;")
    assert "CASCADE" not in rollback.upper()
    assert "disposable/safe qualification targets only" in rollback
    assert "email_verification_challenge" not in rollback
    assert "admin_operator" not in rollback
    assert "DROP TABLE IF EXISTS nexilabs_auth.credential_delivery;" in rollback
    assert "DROP TABLE IF EXISTS nexilabs_auth.credential_bundle_secret;" in rollback
    assert "DROP TABLE IF EXISTS nexilabs_auth.credential_bundle;" in rollback


def test_manifest_row_34_when_present_is_exact_and_first_33_are_preserved() -> None:
    root = _root()
    manifest = json.loads((root / "database/migrations/migration_manifest.json").read_text(encoding="utf-8"))
    # This test is intentionally compatible with the file-by-file gate before
    # the manifest append. Once E row 34 exists, it validates exact artifact parity.
    if len(manifest["migrations"]) == 33:
        assert manifest["catalogue_version"] == 17
        return
    assert manifest["catalogue_version"] >= 18
    assert len(manifest["migrations"]) >= 34
    assert [row["sequence_number"] for row in manifest["migrations"][:34]] == list(range(1, 35))
    row = manifest["migrations"][33]
    assert row["migration_id"] == E_MIGRATION_ID
    assert row["milestone_id"] == "M006.10.2"
    assert row["sequence_number"] == E_SEQUENCE
    assert row["depends_on"] == [E_DEPENDENCY]
    assert set(row["expected_objects"]["tables"]) == REQUIRED_E_TABLES
    assert set(row["expected_objects"]["indexes"]) == REQUIRED_E_INDEXES
    assert set(row["expected_objects"]["constraints"]) == {
        f"nexilabs_auth.{name}" for name in REQUIRED_E_CONSTRAINTS
    }
    assert set(row["expected_objects"]["functions"]) == {
        f"nexilabs_auth.{name}" for name in REQUIRED_E_FUNCTIONS
    }
    for filename, hash_key, size_key in (
        (E_FORWARD_FILE, "forward_sha256", "forward_byte_size"),
        (E_ROLLBACK_FILE, "rollback_sha256", "rollback_byte_size"),
    ):
        raw = (root / "database/migrations" / filename).read_bytes()
        assert row[hash_key] == sha256(raw).hexdigest()
        assert row[size_key] == len(raw)
