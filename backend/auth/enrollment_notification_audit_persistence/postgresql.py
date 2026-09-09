"""P006.UI.10.2.F — read-only PostgreSQL enrollment notification/audit authority.

This adapter exposes durable evidence only. It does not create lifecycle events,
send or render mail, call a mail provider, generate/upload audit artifacts, expose
public URLs, activate accounts, or mutate notification/export lifecycle state.
"""
from __future__ import annotations

from typing import Any

from .contracts import AuditExportRecord, EnrollmentEventRecord, NotificationDeliveryRecord


class PostgreSQLEnrollmentNotificationAuditAuthority:
    """Read-only mapping boundary over P006.UI.10.2.F persistence authority."""

    _EVENT_COLUMNS = """
        e.event_id, e.request_id, e.event_type, e.authority_type, e.authority_id,
        e.occurred_at, e.source_reference, e.correlation_id, e.causation_event_id
    """
    _NOTIFICATION_COLUMNS = """
        n.notification_id, n.event_id, n.template_code, n.template_version,
        n.recipient_reference, n.provider_message_reference, n.delivery_state,
        n.queued_at, n.sent_at, n.failed_at, n.failure_code
    """
    _AUDIT_COLUMNS = """
        a.export_id, a.requested_by_admin_operator_id, a.report_type,
        a.filter_reference, a.object_provider_code, a.object_key,
        a.content_sha256, a.byte_size, a.export_state, a.generated_at,
        a.expires_at, a.retention_until, a.expired_at, a.retired_at
    """

    _EVENT_BY_ID_SQL = f"""
        SELECT {_EVENT_COLUMNS}
        FROM nexilabs_auth.enrollment_event AS e
        WHERE e.event_id = %s
        LIMIT 1
    """
    _EVENTS_FOR_REQUEST_SQL = f"""
        SELECT {_EVENT_COLUMNS}
        FROM nexilabs_auth.enrollment_event AS e
        WHERE e.request_id = %s
        ORDER BY e.occurred_at, e.event_id
    """
    _NOTIFICATION_BY_ID_SQL = f"""
        SELECT {_NOTIFICATION_COLUMNS}
        FROM nexilabs_auth.notification_delivery AS n
        WHERE n.notification_id = %s
        LIMIT 1
    """
    _NOTIFICATIONS_FOR_EVENT_SQL = f"""
        SELECT {_NOTIFICATION_COLUMNS}
        FROM nexilabs_auth.notification_delivery AS n
        WHERE n.event_id = %s
        ORDER BY n.queued_at, n.notification_id
    """
    _AUDIT_EXPORT_BY_ID_SQL = f"""
        SELECT {_AUDIT_COLUMNS}
        FROM nexilabs_auth.audit_export AS a
        WHERE a.export_id = %s
        LIMIT 1
    """
    _AUDIT_EXPORTS_FOR_ADMIN_SQL = f"""
        SELECT {_AUDIT_COLUMNS}
        FROM nexilabs_auth.audit_export AS a
        WHERE a.requested_by_admin_operator_id = %s
        ORDER BY a.generated_at DESC, a.export_id
    """

    def __init__(self, pool: Any) -> None:
        if pool is None or not callable(getattr(pool, "connection", None)):
            raise TypeError("pool with connection(read_only=True) is required")
        self.pool = pool

    @staticmethod
    def _clean_identifier(value: object) -> str | None:
        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _iso(value: object | None) -> str | None:
        if value is None:
            return None
        isoformat = getattr(value, "isoformat", None)
        return str(isoformat()) if callable(isoformat) else str(value)

    @classmethod
    def _event_record(cls, row: tuple[Any, ...] | None) -> EnrollmentEventRecord | None:
        if row is None:
            return None
        return EnrollmentEventRecord(
            event_id=str(row[0]),
            request_id=str(row[1]),
            event_type=str(row[2]),
            authority_type=str(row[3]),
            authority_id=str(row[4]),
            occurred_at=cls._iso(row[5]) or "",
            source_reference=str(row[6]),
            correlation_id=None if row[7] is None else str(row[7]),
            causation_event_id=None if row[8] is None else str(row[8]),
        )

    @classmethod
    def _notification_record(
        cls, row: tuple[Any, ...] | None
    ) -> NotificationDeliveryRecord | None:
        if row is None:
            return None
        return NotificationDeliveryRecord(
            notification_id=str(row[0]),
            event_id=str(row[1]),
            template_code=str(row[2]),
            template_version=int(row[3]),
            recipient_reference=str(row[4]),
            provider_message_reference=None if row[5] is None else str(row[5]),
            delivery_state=str(row[6]),
            queued_at=cls._iso(row[7]) or "",
            sent_at=cls._iso(row[8]),
            failed_at=cls._iso(row[9]),
            failure_code=None if row[10] is None else str(row[10]),
        )

    @classmethod
    def _audit_record(cls, row: tuple[Any, ...] | None) -> AuditExportRecord | None:
        if row is None:
            return None
        return AuditExportRecord(
            export_id=str(row[0]),
            requested_by_admin_operator_id=str(row[1]),
            report_type=str(row[2]),
            filter_reference=str(row[3]),
            object_provider_code=str(row[4]),
            object_key=str(row[5]),
            content_sha256=str(row[6]),
            byte_size=int(row[7]),
            export_state=str(row[8]),
            generated_at=cls._iso(row[9]) or "",
            expires_at=cls._iso(row[10]) or "",
            retention_until=cls._iso(row[11]) or "",
            expired_at=cls._iso(row[12]),
            retired_at=cls._iso(row[13]),
        )

    def event_by_id(self, event_id: str) -> EnrollmentEventRecord | None:
        value = self._clean_identifier(event_id)
        if value is None:
            return None
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._EVENT_BY_ID_SQL, (value,))
                row = cursor.fetchone()
        return self._event_record(row)

    def events_for_request(self, request_id: str) -> tuple[EnrollmentEventRecord, ...]:
        value = self._clean_identifier(request_id)
        if value is None:
            return ()
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._EVENTS_FOR_REQUEST_SQL, (value,))
                rows = list(cursor.fetchall())
        return tuple(record for row in rows if (record := self._event_record(row)) is not None)

    def notification_by_id(self, notification_id: str) -> NotificationDeliveryRecord | None:
        value = self._clean_identifier(notification_id)
        if value is None:
            return None
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._NOTIFICATION_BY_ID_SQL, (value,))
                row = cursor.fetchone()
        return self._notification_record(row)

    def notifications_for_event(self, event_id: str) -> tuple[NotificationDeliveryRecord, ...]:
        value = self._clean_identifier(event_id)
        if value is None:
            return ()
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._NOTIFICATIONS_FOR_EVENT_SQL, (value,))
                rows = list(cursor.fetchall())
        return tuple(
            record for row in rows if (record := self._notification_record(row)) is not None
        )

    def audit_export_by_id(self, export_id: str) -> AuditExportRecord | None:
        value = self._clean_identifier(export_id)
        if value is None:
            return None
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._AUDIT_EXPORT_BY_ID_SQL, (value,))
                row = cursor.fetchone()
        return self._audit_record(row)

    def audit_exports_for_admin(self, admin_operator_id: str) -> tuple[AuditExportRecord, ...]:
        value = self._clean_identifier(admin_operator_id)
        if value is None:
            return ()
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._AUDIT_EXPORTS_FOR_ADMIN_SQL, (value,))
                rows = list(cursor.fetchall())
        return tuple(record for row in rows if (record := self._audit_record(row)) is not None)


__all__ = ["PostgreSQLEnrollmentNotificationAuditAuthority"]
