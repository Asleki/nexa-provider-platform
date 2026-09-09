from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re


F_MIGRATION_ID = "m006_10_02_enrollment_notification_audit_persistence"
F_FORWARD_FILE = f"{F_MIGRATION_ID}.sql"
F_ROLLBACK_FILE = f"{F_MIGRATION_ID}_rollback.sql"
F_SEQUENCE = 35
F_DEPENDENCY = "m006_10_02_credential_bundle_storage_delivery"

REQUIRED_F_TABLES = {
    "nexilabs_auth.enrollment_event",
    "nexilabs_auth.notification_delivery",
    "nexilabs_auth.audit_export",
}
REQUIRED_F_INDEXES = {
    "ux_nexilabs_auth_enrollment_event_authority",
    "ix_nexilabs_auth_enrollment_event_request",
    "ix_nexilabs_auth_enrollment_event_authority",
    "ix_nexilabs_auth_enrollment_event_correlation",
    "ix_nexilabs_auth_notification_delivery_event",
    "ix_nexilabs_auth_notification_delivery_state",
    "ix_nexilabs_auth_notification_delivery_template",
    "ux_nexilabs_auth_audit_export_object",
    "ix_nexilabs_auth_audit_export_admin",
    "ix_nexilabs_auth_audit_export_state_expiry",
}
REQUIRED_F_FUNCTIONS = {
    "validate_enrollment_event_authority",
    "reject_enrollment_event_mutation",
    "validate_notification_event_template",
    "validate_notification_delivery_transition",
    "validate_audit_export_requester",
    "validate_audit_export_transition",
}
REQUIRED_F_TRIGGERS = {
    "tr_nexilabs_auth_enrollment_event_authority",
    "tr_nexilabs_auth_enrollment_event_immutable",
    "tr_nexilabs_auth_notification_event_template",
    "tr_nexilabs_auth_notification_delivery_transition",
    "tr_nexilabs_auth_audit_export_requester",
    "tr_nexilabs_auth_audit_export_transition",
}
REQUIRED_F_CONSTRAINTS = {
    "fk_nexilabs_auth_enrollment_event_request",
    "fk_nexilabs_auth_enrollment_event_causation",
    "ck_nexilabs_auth_enrollment_event_id_nonblank",
    "ck_nexilabs_auth_enrollment_event_type",
    "ck_nexilabs_auth_enrollment_event_authority_type",
    "ck_nexilabs_auth_enrollment_event_authority_id",
    "ck_nexilabs_auth_enrollment_event_source_reference",
    "ck_nexilabs_auth_enrollment_event_correlation",
    "ck_nexilabs_auth_enrollment_event_causation_not_self",
    "fk_nexilabs_auth_notification_delivery_event",
    "ck_nexilabs_auth_notification_id_nonblank",
    "ck_nexilabs_auth_notification_template",
    "ck_nexilabs_auth_notification_template_version",
    "ck_nexilabs_auth_notification_recipient_reference",
    "ck_nexilabs_auth_notification_provider_reference",
    "ck_nexilabs_auth_notification_delivery_state",
    "ck_nexilabs_auth_notification_terminal_evidence",
    "fk_nexilabs_auth_audit_export_admin_operator",
    "ck_nexilabs_auth_audit_export_id_nonblank",
    "ck_nexilabs_auth_audit_export_report_type",
    "ck_nexilabs_auth_audit_export_filter_reference",
    "ck_nexilabs_auth_audit_export_object_provider",
    "ck_nexilabs_auth_audit_export_object_key",
    "ck_nexilabs_auth_audit_export_sha256",
    "ck_nexilabs_auth_audit_export_byte_size",
    "ck_nexilabs_auth_audit_export_state",
    "ck_nexilabs_auth_audit_export_retention",
    "ck_nexilabs_auth_audit_export_state_timestamps",
    "ck_nexilabs_auth_audit_export_expired_time",
    "ck_nexilabs_auth_audit_export_retired_time",
}
EVENT_TYPES = (
    "REQUEST_RECEIVED", "UNDER_REVIEW", "APPROVED", "REJECTED",
    "SETUP_ISSUED", "SETUP_VERIFIED", "OTP_ISSUED", "EMAIL_VERIFIED",
    "ENIGMA_PROVISIONED", "BUNDLE_READY", "DELIVERY_ISSUED", "ACCOUNT_ACTIVATED",
)
TEMPLATES = (
    "DEVELOPER_REQUEST_RECEIVED", "ADMIN_DEVELOPER_REQUEST_ALERT",
    "DEVELOPER_REQUEST_APPROVED", "DEVELOPER_REQUEST_REJECTED",
    "DEVELOPER_SETUP_ISSUED", "EMAIL_VERIFICATION_OTP",
    "CREDENTIAL_BUNDLE_READY", "DEVELOPER_WELCOME", "SECURITY_ALERT",
)


def _root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "database/migrations" / F_FORWARD_FILE).is_file():
            return candidate
    raise AssertionError("repository root not found")


def _sql() -> str:
    return (_root() / "database/migrations" / F_FORWARD_FILE).read_text(encoding="utf-8")


def _table_sql(name: str) -> str:
    match = re.search(
        rf"CREATE TABLE nexilabs_auth\.{re.escape(name)}\s*\((.*?)\n\);",
        _sql(), re.S,
    )
    assert match is not None
    return match.group(1)


def test_f_forward_is_additive_zero_seed_and_exactly_three_tables() -> None:
    sql = _sql()
    assert sql.startswith("BEGIN;\n") and sql.rstrip().endswith("COMMIT;")
    tables = set(re.findall(r"CREATE TABLE\s+([a-z0-9_.]+)\s*\(", sql, re.I))
    assert tables == REQUIRED_F_TABLES
    assert not re.search(r"\bINSERT\s+INTO\b", sql, re.I)
    assert "CREATE SCHEMA" not in sql.upper()
    for table in REQUIRED_F_TABLES:
        assert f"REVOKE ALL ON TABLE {table} FROM PUBLIC;" in sql


def test_enrollment_event_vocabulary_is_exact_append_only_and_predecessor_referenced() -> None:
    sql = _sql()
    table = _table_sql("enrollment_event")
    for value in EVENT_TYPES:
        assert f"'{value}'" in table
    quoted = set(re.findall(r"'([A-Z][A-Z0-9_]+)'", re.search(
        r"CONSTRAINT ck_nexilabs_auth_enrollment_event_type CHECK \((.*?)\n    \),",
        table, re.S,
    ).group(1)))
    assert quoted == set(EVENT_TYPES)
    assert "REFERENCES nexilabs_auth.developer_access_request(request_id)" in table
    assert "enrollment events are immutable append-only authority" in sql
    assert "BEFORE UPDATE OR DELETE\nON nexilabs_auth.enrollment_event" in sql
    for authority in (
        "developer_access_decision", "developer_setup", "email_verification_challenge",
        "principal_enigma_profile", "credential_bundle", "credential_delivery", "principal_account",
    ):
        assert f"nexilabs_auth.{authority}" in sql


def test_event_provenance_and_correlation_are_opaque_non_pii_references() -> None:
    sql = _sql()
    assert "source_reference !~ '@'" in sql
    assert "source_reference !~ '[[:space:]]'" in sql
    assert "source_reference !~ '^[a-zA-Z][a-zA-Z0-9+.-]*://'" in sql
    assert "correlation_id !~ '@'" in sql
    assert "correlation_id !~ '[[:space:]]'" in sql
    assert "causation_event_id IS NULL OR causation_event_id <> event_id" in sql
    assert "causation event must belong to the same request and not occur later" in sql


def test_notification_contract_is_provider_neutral_reference_only_and_body_free() -> None:
    sql = _sql()
    table = _table_sql("notification_delivery")
    for code in TEMPLATES:
        assert f"'{code}'" in table
    for forbidden in (
        "email_address", "mailbox", "message_body", "rendered_body", "html_body",
        "text_body", "password", "otp_value", "developer_setup_secret",
        "archive_password", "enigma_response", "raw_download_token", "provider_credential",
    ):
        assert forbidden not in table.lower()
    assert "recipient_reference !~ '@'" in table
    assert "recipient_reference !~ '[[:space:]]'" in table
    assert "provider_message_reference !~ '@'" in table
    assert "provider_message_reference !~ '[[:space:]]'" in table
    assert "NEXILABS_ADMIN_OPERATIONS" in sql
    assert "operations notification must use logical operations recipient reference" in sql
    assert "applicant notification cannot use operations recipient reference" in sql
    assert "terminal notification delivery evidence is immutable" in sql


def test_notification_templates_are_bound_to_the_lifecycle_events_that_cause_them() -> None:
    sql = _sql()
    expected = {
        "DEVELOPER_REQUEST_RECEIVED": "REQUEST_RECEIVED",
        "ADMIN_DEVELOPER_REQUEST_ALERT": "REQUEST_RECEIVED",
        "DEVELOPER_REQUEST_APPROVED": "APPROVED",
        "DEVELOPER_REQUEST_REJECTED": "REJECTED",
        "DEVELOPER_SETUP_ISSUED": "SETUP_ISSUED",
        "EMAIL_VERIFICATION_OTP": "OTP_ISSUED",
        "CREDENTIAL_BUNDLE_READY": "BUNDLE_READY",
        "DEVELOPER_WELCOME": "ACCOUNT_ACTIVATED",
    }
    for template, event in expected.items():
        assert f"NEW.template_code = '{template}'" in sql
        assert f"event_type_value IS DISTINCT FROM '{event}'" in sql
    assert "NEW.template_code IN ('ADMIN_DEVELOPER_REQUEST_ALERT', 'SECURITY_ALERT')" in sql


def test_audit_export_is_active_admin_owned_private_integrity_and_retention_authority() -> None:
    sql = _sql()
    table = _table_sql("audit_export")
    assert "REFERENCES nexilabs_auth.admin_operator(admin_operator_id)" in table
    assert "operator_state_value IS DISTINCT FROM 'ACTIVE'" in sql
    assert "filter_reference ~ '^[A-Z][A-Z0-9_]{2,79}:" in table
    assert "object_key !~ '^[a-zA-Z][a-zA-Z0-9+.-]*://'" in table
    assert "content_sha256 ~ '^[0-9a-f]{64}$'" in table
    assert "byte_size > 0" in table
    assert "retention_until >= expires_at" in table
    assert "retired_at IS NULL OR retired_at >= retention_until" in table
    assert "expired audit export cannot become available again" in sql
    assert "audit export metadata is durable authority and cannot be deleted" in sql
    assert "report bytes remain outside PostgreSQL" in sql


def test_f_sql_contains_no_mail_provider_secret_report_bytes_or_public_url_authority() -> None:
    sql = _sql().lower()
    assert "bytea" not in sql
    for forbidden in (
        "smtp_password", "provider_api_key", "provider_secret", "gmail_password",
        "mail_body", "rendered_body", "raw_otp", "raw_token", "archive_password text",
        "public_url text", "presigned_url text", "artifact_bytes",
    ):
        assert forbidden not in sql
    assert "never a public, permanent or presigned url" in sql


def test_required_indexes_constraints_functions_triggers_and_narrow_rollback_are_exact() -> None:
    sql = _sql()
    indexes = set(re.findall(r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+([a-z0-9_]+)", sql, re.I))
    constraints = set(re.findall(r"CONSTRAINT\s+([a-z0-9_]+)", sql, re.I))
    functions = set(re.findall(r"CREATE FUNCTION\s+nexilabs_auth\.([a-z0-9_]+)", sql, re.I))
    triggers = set(re.findall(r"CREATE TRIGGER\s+([a-z0-9_]+)", sql, re.I))
    assert indexes == REQUIRED_F_INDEXES
    assert constraints == REQUIRED_F_CONSTRAINTS
    assert functions == REQUIRED_F_FUNCTIONS
    assert triggers == REQUIRED_F_TRIGGERS
    rollback = (_root() / "database/migrations" / F_ROLLBACK_FILE).read_text(encoding="utf-8")
    assert rollback.startswith("BEGIN;\n") and rollback.rstrip().endswith("COMMIT;")
    assert "CASCADE" not in rollback.upper()
    assert "disposable/safe qualification targets only" in rollback
    for predecessor in (
        "credential_bundle", "email_verification_challenge", "admin_operator",
        "developer_access_decision", "developer_access_request",
    ):
        assert f"DROP TABLE IF EXISTS nexilabs_auth.{predecessor};" not in rollback
    for table in ("audit_export", "notification_delivery", "enrollment_event"):
        assert f"DROP TABLE IF EXISTS nexilabs_auth.{table};" in rollback


def test_manifest_row_35_when_present_is_exact_and_first_34_are_preserved() -> None:
    root = _root()
    manifest = json.loads((root / "database/migrations/migration_manifest.json").read_text(encoding="utf-8"))
    if len(manifest["migrations"]) == 34:
        assert manifest["catalogue_version"] == 18
        return
    assert manifest["catalogue_version"] >= 19
    assert len(manifest["migrations"]) >= 35
    assert [row["sequence_number"] for row in manifest["migrations"][:35]] == list(range(1, 36))
    row = manifest["migrations"][34]
    assert row["migration_id"] == F_MIGRATION_ID
    assert row["milestone_id"] == "M006.10.2"
    assert row["sequence_number"] == F_SEQUENCE
    assert row["depends_on"] == [F_DEPENDENCY]
    assert set(row["expected_objects"]["tables"]) == REQUIRED_F_TABLES
    assert set(row["expected_objects"]["indexes"]) == REQUIRED_F_INDEXES
    assert set(row["expected_objects"]["constraints"]) == {
        f"nexilabs_auth.{name}" for name in REQUIRED_F_CONSTRAINTS
    }
    assert set(row["expected_objects"]["functions"]) == {
        f"nexilabs_auth.{name}" for name in REQUIRED_F_FUNCTIONS
    }
    for filename, hash_key, size_key in (
        (F_FORWARD_FILE, "forward_sha256", "forward_byte_size"),
        (F_ROLLBACK_FILE, "rollback_sha256", "rollback_byte_size"),
    ):
        raw = (root / "database/migrations" / filename).read_bytes()
        assert row[hash_key] == sha256(raw).hexdigest()
        assert row[size_key] == len(raw)
