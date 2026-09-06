from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re


D_MIGRATION_ID = "m006_10_02_email_verification_challenge"
D_FORWARD_FILE = f"{D_MIGRATION_ID}.sql"
D_ROLLBACK_FILE = f"{D_MIGRATION_ID}_rollback.sql"
D_SEQUENCE = 33
D_DEPENDENCY = "m006_10_02_layered_admin_review_authority"

REQUIRED_D_INDEXES = {
    "ux_nexilabs_auth_issued_email_verification_challenge",
    "ix_nexilabs_auth_email_verification_challenge_principal",
    "ix_nexilabs_auth_email_verification_challenge_state_expiry",
}
REQUIRED_D_FUNCTIONS = {
    "validate_email_verification_challenge_email",
    "validate_email_verification_challenge_transition",
}
REQUIRED_D_CONSTRAINTS = {
    "fk_nexilabs_auth_email_challenge_principal",
    "fk_nexilabs_auth_email_challenge_owner",
    "ck_nexilabs_auth_email_challenge_id_nonblank",
    "ck_nexilabs_auth_otp_verifier_scheme",
    "ck_nexilabs_auth_otp_verifier_version",
    "ck_nexilabs_auth_otp_verifier_payload",
    "ck_nexilabs_auth_otp_challenge_state",
    "ck_nexilabs_auth_otp_policy_version",
    "ck_nexilabs_auth_otp_expiry",
    "ck_nexilabs_auth_otp_attempts",
    "ck_nexilabs_auth_otp_state_timestamps",
    "ck_nexilabs_auth_otp_verified_time",
    "ck_nexilabs_auth_otp_invalidated_time",
    "ck_nexilabs_auth_otp_resend_accounting",
}


def _root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "database/migrations" / D_FORWARD_FILE).is_file():
            return candidate
    raise AssertionError("repository root not found")


def _sql() -> str:
    return (_root() / "database/migrations" / D_FORWARD_FILE).read_text(encoding="utf-8")


def test_d_forward_is_additive_zero_seed_public_denied_and_one_table_only() -> None:
    sql = _sql()
    assert sql.startswith("BEGIN;\n") and sql.rstrip().endswith("COMMIT;")
    tables = set(re.findall(r"CREATE TABLE\s+([a-z0-9_.]+)\s*\(", sql, re.I))
    assert tables == {"nexilabs_auth.email_verification_challenge"}
    assert not re.search(r"\bINSERT\s+INTO\b", sql, re.I)
    assert "CREATE SCHEMA" not in sql.upper()
    assert "REVOKE ALL ON TABLE nexilabs_auth.email_verification_challenge FROM PUBLIC;" in sql
    assert "REVOKE ALL ON ALL FUNCTIONS IN SCHEMA nexilabs_auth FROM PUBLIC;" in sql


def test_challenge_is_bound_to_same_owner_principal_email_and_does_not_require_active_principal() -> None:
    sql = _sql()
    assert "FOREIGN KEY (email_id, principal_id)" in sql
    assert "REFERENCES nexilabs_auth.account_email(email_id, principal_id)" in sql
    assert "FOREIGN KEY (principal_id)" in sql
    assert "REFERENCES nexilabs_auth.principal_account(principal_id)" in sql
    assert "account_state = 'ACTIVE'" not in sql
    assert "identity_type" not in sql
    assert "verification_state" in sql and "'REVOKED'" in sql


def test_raw_otp_has_no_column_and_verifier_contract_rejects_plaintext_scheme_and_short_payload() -> None:
    sql = _sql()
    create = re.search(
        r"CREATE TABLE nexilabs_auth\.email_verification_challenge\s*\((.*?)\n\);",
        sql,
        re.S,
    )
    assert create is not None
    table_sql = create.group(1)
    assert "raw_otp" not in table_sql.lower()
    assert "otp_plaintext" not in table_sql.lower()
    assert "otp_verifier_scheme" in table_sql
    assert "otp_verifier_version" in table_sql
    assert "otp_verifier_payload" in table_sql
    assert "'plaintext'" in table_sql and "'cleartext'" in table_sql and "'reversible'" in table_sql
    assert "length(otp_verifier_payload) BETWEEN 20 AND 4096" in table_sql
    assert "raw OTP and verifier key/pepper remain outside PostgreSQL" in sql


def test_lifecycle_timing_attempt_resend_and_terminal_history_constraints_are_present() -> None:
    sql = _sql()
    for state in ("ISSUED", "VERIFIED", "EXPIRED", "LOCKED", "INVALIDATED"):
        assert f"'{state}'" in sql
    for name in REQUIRED_D_CONSTRAINTS:
        assert name in sql
    assert "expires_at > issued_at" in sql
    assert "attempt_count BETWEEN 0 AND max_attempts" in sql
    assert "challenge_state <> 'LOCKED' OR attempt_count = max_attempts" in sql
    assert "resend_count = 0" in sql and "last_resend_at IS NULL" in sql
    assert "last_resend_at <= expires_at" in sql
    assert "WHERE challenge_state = 'ISSUED'" in sql
    assert "terminal email verification challenges are immutable" in sql
    assert "BEFORE UPDATE OR DELETE" in sql
    assert "durable authority and cannot be deleted" in sql
    assert "expiry cannot move backwards" in sql
    assert "attempt/resend counters cannot decrease" in sql


def test_required_indexes_functions_and_rollback_are_narrow() -> None:
    sql = _sql()
    indexes = set(re.findall(r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+([a-z0-9_]+)", sql, re.I))
    functions = set(re.findall(r"CREATE FUNCTION\s+nexilabs_auth\.([a-z0-9_]+)", sql, re.I))
    assert indexes == REQUIRED_D_INDEXES
    assert functions == REQUIRED_D_FUNCTIONS
    rollback = (_root() / "database/migrations" / D_ROLLBACK_FILE).read_text(encoding="utf-8")
    assert rollback.startswith("BEGIN;\n") and rollback.rstrip().endswith("COMMIT;")
    assert "CASCADE" not in rollback.upper()
    assert "disposable/safe qualification targets only" in rollback
    assert "admin_operator" not in rollback
    assert "developer_access_decision" not in rollback
    assert "DROP TABLE IF EXISTS nexilabs_auth.email_verification_challenge;" in rollback


def test_d_manifest_row_33_is_exact_and_first_32_are_preserved() -> None:
    root = _root()
    path = root / "database/migrations/migration_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["catalogue_version"] >= 17
    assert len(manifest["migrations"]) >= 33
    assert [row["sequence_number"] for row in manifest["migrations"][:33]] == list(range(1, 34))
    row = manifest["migrations"][32]
    assert row["migration_id"] == D_MIGRATION_ID
    assert row["milestone_id"] == "M006.10.2"
    assert row["sequence_number"] == D_SEQUENCE
    assert row["depends_on"] == [D_DEPENDENCY]
    assert set(row["expected_objects"]["tables"]) == {"nexilabs_auth.email_verification_challenge"}
    assert set(row["expected_objects"]["indexes"]) == REQUIRED_D_INDEXES
    assert set(row["expected_objects"]["constraints"]) == {
        f"nexilabs_auth.{x}" for x in REQUIRED_D_CONSTRAINTS
    }
    assert set(row["expected_objects"]["functions"]) == {
        f"nexilabs_auth.{x}" for x in REQUIRED_D_FUNCTIONS
    }
    for filename, hash_key, size_key in (
        (D_FORWARD_FILE, "forward_sha256", "forward_byte_size"),
        (D_ROLLBACK_FILE, "rollback_sha256", "rollback_byte_size"),
    ):
        raw = (root / "database/migrations" / filename).read_bytes()
        assert row[hash_key] == sha256(raw).hexdigest()
        assert row[size_key] == len(raw)
