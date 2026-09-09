from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import inspect

from backend.auth.enrollment_notification_audit_persistence.postgresql import (
    PostgreSQLEnrollmentNotificationAuditAuthority,
)

NOW = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)
EVENT_ROW = (
    "event-1", "request-1", "APPROVED", "DEVELOPER_ACCESS_DECISION",
    "decision-1", NOW, "receipt:event-1", "correlation-1", None,
)
NOTIFICATION_ROW = (
    "notification-1", "event-1", "DEVELOPER_REQUEST_APPROVED", 1,
    "DEVELOPER_ACCESS_REQUEST:request-1", "provider-message-1", "SENT",
    NOW, NOW, None, None,
)
AUDIT_ROW = (
    "export-1", "admin-operator-1", "DEVELOPER_ENROLLMENT_AUDIT",
    "AUDIT_FILTER:developer-enrollment-1", "AWS_S3_PRIVATE",
    "private/audit/export-1.pdf", "a" * 64, 4096, "AVAILABLE",
    NOW, NOW, NOW, None, None,
)


class Cursor:
    def __init__(self, *, one=None, many=None):
        self.one = one
        self.many = [] if many is None else list(many)
        self.calls: list[tuple[str, object]] = []
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, sql, params=None): self.calls.append((" ".join(str(sql).split()), params))
    def fetchone(self): return self.one
    def fetchall(self): return list(self.many)


class Connection:
    def __init__(self, cursor): self.cursor_obj = cursor
    def cursor(self): return self.cursor_obj


class Pool:
    def __init__(self, cursor): self.cursor_obj = cursor; self.read_only: list[bool] = []
    @contextmanager
    def connection(self, read_only=False):
        self.read_only.append(read_only)
        yield Connection(self.cursor_obj)


def test_event_reads_are_request_scoped_ordered_and_safe() -> None:
    cursor = Cursor(many=[EVENT_ROW])
    pool = Pool(cursor)
    rows = PostgreSQLEnrollmentNotificationAuditAuthority(pool).events_for_request(" request-1 ")
    assert len(rows) == 1 and rows[0].event_type == "APPROVED"
    sql, params = cursor.calls[0]
    assert "e.request_id = %s" in sql and "ORDER BY e.occurred_at, e.event_id" in sql
    assert params == ("request-1",)
    assert pool.read_only == [True]


def test_notification_maps_provider_evidence_but_safe_summary_hides_provider_reference() -> None:
    cursor = Cursor(one=NOTIFICATION_ROW)
    record = PostgreSQLEnrollmentNotificationAuditAuthority(Pool(cursor)).notification_by_id("notification-1")
    assert record is not None and record.delivery_state == "SENT"
    assert record.provider_message_reference == "provider-message-1"
    assert record.safe_summary()["providerMessageReferencePresent"] is True
    assert "provider-message-1" not in repr(record)


def test_audit_maps_integrity_and_retention_but_safe_summary_hides_private_refs() -> None:
    cursor = Cursor(one=AUDIT_ROW)
    record = PostgreSQLEnrollmentNotificationAuditAuthority(Pool(cursor)).audit_export_by_id("export-1")
    assert record is not None
    assert record.content_sha256 == "a" * 64 and record.byte_size == 4096
    summary = record.safe_summary()
    assert "objectKey" not in summary and "filterReference" not in summary
    assert "private/audit" not in repr(record)


def test_blank_identifiers_never_borrow_database_connection() -> None:
    pool = Pool(Cursor())
    authority = PostgreSQLEnrollmentNotificationAuditAuthority(pool)
    assert authority.event_by_id(" ") is None
    assert authority.events_for_request("\t") == ()
    assert authority.notification_by_id("") is None
    assert authority.notifications_for_event("\n") == ()
    assert authority.audit_export_by_id(" ") is None
    assert authority.audit_exports_for_admin("") == ()
    assert pool.read_only == []


def test_adapter_has_no_write_mail_provider_export_generation_or_activation_surface() -> None:
    text = inspect.getsource(PostgreSQLEnrollmentNotificationAuditAuthority)
    upper = text.upper()
    for verb in ("INSERT INTO", "UPDATE ", "DELETE FROM"):
        assert verb not in upper
    for name in (
        "send_mail", "render_mail", "retry_mail", "provider_credentials",
        "generate_export", "upload_export", "presign", "activate_account",
        "create_event", "record_notification", "update_delivery",
    ):
        assert not hasattr(PostgreSQLEnrollmentNotificationAuditAuthority, name)
