from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

from backend.auth.admin_review_persistence.qualification import (
    C_FORWARD_FILE,
    C_MIGRATION_ID,
    C_ROLLBACK_FILE,
    REQUIRED_C_CONSTRAINTS,
    REQUIRED_C_FUNCTIONS,
    REQUIRED_C_INDEXES,
)


def _root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "database/migrations" / C_FORWARD_FILE).is_file():
            return candidate
    raise AssertionError("repository root not found")


def _sql() -> str:
    return (_root() / "database/migrations" / C_FORWARD_FILE).read_text(encoding="utf-8")


def test_c_forward_is_additive_zero_seed_and_public_denied() -> None:
    sql = _sql()
    assert sql.startswith("BEGIN;\n") and sql.rstrip().endswith("COMMIT;")
    tables = set(re.findall(r"CREATE TABLE\s+([a-z0-9_.]+)\s*\(", sql, re.I))
    assert tables == {"nexilabs_auth.admin_operator", "nexilabs_auth.developer_access_decision"}
    assert not re.search(r"\bINSERT\s+INTO\b", sql, re.I)
    assert "CREATE SCHEMA" not in sql.upper()
    assert "REVOKE ALL ON TABLE nexilabs_auth.admin_operator FROM PUBLIC;" in sql
    assert "REVOKE ALL ON TABLE nexilabs_auth.developer_access_decision FROM PUBLIC;" in sql
    assert "REVOKE ALL ON ALL FUNCTIONS IN SCHEMA nexilabs_auth FROM PUBLIC;" in sql


def test_admin_operator_is_layered_on_nexadevs_principal_and_verified_same_owner_email() -> None:
    sql = _sql()
    assert "nexadevs_developer" in sql
    assert "nexilabs_admin" not in sql
    assert "production" not in sql.lower()
    assert "simulation" not in sql.lower()
    assert "FOREIGN KEY (bound_admin_email_id, principal_id)" in sql
    assert "REFERENCES nexilabs_auth.account_email(email_id, principal_id)" in sql
    assert "verification_state" in sql and "'VERIFIED'" in sql
    assert "principal_state IS DISTINCT FROM 'ACTIVE'" in sql
    assert "admin_developer_id_key = lower(btrim(admin_developer_id))" in sql


def test_admin_password_is_independent_active_credential_kind() -> None:
    sql = _sql()
    assert "ux_nexilabs_auth_active_admin_password" in sql
    assert "credential_kind = 'ADMIN_PASSWORD'" in sql
    assert "credential_kind='password'" in sql.replace(" ", "")
    # C does not rewrite or drop the historical Developer-password index.
    assert "DROP INDEX" not in sql.upper()


def test_terminal_decision_requires_real_reviewer_policy_receipt_and_exact_reason_model() -> None:
    sql = _sql()
    for name in REQUIRED_C_CONSTRAINTS:
        assert name in sql
    for code in (
        "DUPLICATE_ACTIVE_REQUEST",
        "IDENTITY_NOT_CONFIRMED",
        "ACCESS_ELIGIBILITY_NOT_CONFIRMED",
        "SECURITY_REVIEW_FAILED",
        "PREVIOUS_ACCESS_RESTRICTION",
        "REQUEST_INCOMPLETE",
        "POLICY_REQUIREMENTS_NOT_MET",
    ):
        assert code in sql
    for technical in ("INVALID_SETUP", "EXPIRED_SETUP", "WRONG_OTP", "EXPIRED_OTP"):
        assert technical not in sql
    assert "FOREIGN KEY (admin_operator_id, reviewer_principal_id)" in sql
    assert "Developer access decision requires an ACTIVE reviewer Admin Operator" in sql
    assert "terminal_decision_id" in sql
    assert "receipt_reference" in sql and "policy_version" in sql and "internal_reference" in sql


def test_decision_history_is_append_only_and_rollback_has_no_cascade() -> None:
    sql = _sql()
    assert "BEFORE UPDATE OR DELETE" in sql
    assert "Developer access decisions are immutable append-only authority" in sql
    assert REQUIRED_C_FUNCTIONS.issubset(set(re.findall(r"CREATE FUNCTION\s+nexilabs_auth\.([a-z0-9_]+)", sql, re.I)))
    assert REQUIRED_C_INDEXES.issubset(set(re.findall(r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+([a-z0-9_]+)", sql, re.I)))
    rollback = (_root() / "database/migrations" / C_ROLLBACK_FILE).read_text(encoding="utf-8")
    assert rollback.startswith("BEGIN;\n") and rollback.rstrip().endswith("COMMIT;")
    assert "CASCADE" not in rollback.upper()
    assert "disposable/safe qualification targets only" in rollback


def test_c_manifest_row_32_is_exact_and_first_31_are_preserved() -> None:
    root = _root()
    path = root / "database/migrations/migration_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["catalogue_version"] == 16
    assert len(manifest["migrations"]) == 32
    assert [row["sequence_number"] for row in manifest["migrations"]] == list(range(1, 33))
    row = manifest["migrations"][-1]
    assert row["migration_id"] == C_MIGRATION_ID
    assert row["milestone_id"] == "M006.10.2"
    assert row["sequence_number"] == 32
    assert row["depends_on"] == ["m006_10_02_nexilabs_account_credential_authority"]
    assert set(row["expected_objects"]["tables"]) == {
        "nexilabs_auth.admin_operator", "nexilabs_auth.developer_access_decision"
    }
    assert set(row["expected_objects"]["indexes"]) == REQUIRED_C_INDEXES
    assert set(row["expected_objects"]["constraints"]) == {f"nexilabs_auth.{x}" for x in REQUIRED_C_CONSTRAINTS}
    assert set(row["expected_objects"]["functions"]) == {f"nexilabs_auth.{x}" for x in REQUIRED_C_FUNCTIONS}
    for filename, hash_key, size_key in (
        (C_FORWARD_FILE, "forward_sha256", "forward_byte_size"),
        (C_ROLLBACK_FILE, "rollback_sha256", "rollback_byte_size"),
    ):
        raw = (root / "database/migrations" / filename).read_bytes()
        assert row[hash_key] == sha256(raw).hexdigest()
        assert row[size_key] == len(raw)
