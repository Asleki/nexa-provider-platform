"""P006.UI.10.2.F — PostgreSQL enrollment notification/mail/audit qualification."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from backend.auth.credential_bundle_persistence.qualification import (
    E_MIGRATION_ID,
    E_SEQUENCE,
    POST_E_AUTH_TABLES,
    PostgreSQLCredentialBundleQualification,
)

from .contracts import (
    ADMIN_OPERATIONS_RECIPIENT_REFERENCE,
    EnrollmentNotificationAuditAdapterQualificationReceipt,
    EnrollmentNotificationAuditQualificationError,
    EnrollmentNotificationAuditQualificationReport,
)
from .postgresql import PostgreSQLEnrollmentNotificationAuditAuthority


F_MIGRATION_ID = "m006_10_02_enrollment_notification_audit_persistence"
F_MILESTONE_ID = "M006.10.2"
F_SEQUENCE = 35
F_CATALOGUE_VERSION = 19
F_FORWARD_FILE = f"{F_MIGRATION_ID}.sql"
F_ROLLBACK_FILE = f"{F_MIGRATION_ID}_rollback.sql"
F_DEPENDENCY = E_MIGRATION_ID

POST_F_AUTH_TABLES = tuple(
    sorted((*POST_E_AUTH_TABLES, "enrollment_event", "notification_delivery", "audit_export"))
)

REQUIRED_F_COLUMNS = (
    ("enrollment_event", frozenset({
        "event_id", "request_id", "event_type", "authority_type", "authority_id",
        "occurred_at", "source_reference", "correlation_id", "causation_event_id",
    })),
    ("notification_delivery", frozenset({
        "notification_id", "event_id", "template_code", "template_version",
        "recipient_reference", "provider_message_reference", "delivery_state",
        "queued_at", "sent_at", "failed_at", "failure_code",
    })),
    ("audit_export", frozenset({
        "export_id", "requested_by_admin_operator_id", "report_type",
        "filter_reference", "object_provider_code", "object_key", "content_sha256",
        "byte_size", "export_state", "generated_at", "expires_at",
        "retention_until", "expired_at", "retired_at",
    })),
)

REQUIRED_F_INDEXES = frozenset({
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
})

REQUIRED_F_CONSTRAINTS = frozenset({
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
})

REQUIRED_F_FUNCTIONS = frozenset({
    "validate_enrollment_event_authority",
    "reject_enrollment_event_mutation",
    "validate_notification_event_template",
    "validate_notification_delivery_transition",
    "validate_audit_export_requester",
    "validate_audit_export_transition",
})

REQUIRED_F_TRIGGERS = frozenset({
    "tr_nexilabs_auth_enrollment_event_authority",
    "tr_nexilabs_auth_enrollment_event_immutable",
    "tr_nexilabs_auth_notification_event_template",
    "tr_nexilabs_auth_notification_delivery_transition",
    "tr_nexilabs_auth_audit_export_requester",
    "tr_nexilabs_auth_audit_export_transition",
})


class _ProofRollback(RuntimeError):
    pass


class _BorrowedConnectionPool:
    def __init__(self, connection: Any):
        self.connection_object = connection

    @contextmanager
    def connection(self, read_only: bool = False):
        yield self.connection_object


class PostgreSQLEnrollmentNotificationAuditQualification:
    """Qualify F while treating the complete A-E persistence prefix as immutable."""

    def __init__(self, pool: Any) -> None:
        if pool is None or not callable(getattr(pool, "connection", None)):
            raise TypeError("pool with connection(read_only=...) is required")
        self.pool = pool

    @staticmethod
    def _read_manifest(manifest_path: Path) -> tuple[dict[str, object], ...]:
        try:
            payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise EnrollmentNotificationAuditQualificationError(
                "cannot read the live migration manifest"
            ) from exc
        version = payload.get("catalogue_version")
        if isinstance(version, bool) or not isinstance(version, int) or version < F_CATALOGUE_VERSION:
            raise EnrollmentNotificationAuditQualificationError(
                f"F requires migration catalogue_version >= {F_CATALOGUE_VERSION}"
            )
        rows = payload.get("migrations")
        if not isinstance(rows, list) or len(rows) < F_SEQUENCE:
            raise EnrollmentNotificationAuditQualificationError(
                "F requires at least 35 manifest migrations"
            )
        result = tuple(row for row in rows if isinstance(row, dict))
        if len(result) != len(rows):
            raise EnrollmentNotificationAuditQualificationError(
                "migration manifest contains a malformed row"
            )
        prefix = tuple(int(row.get("sequence_number", -1)) for row in result[:F_SEQUENCE])
        if prefix != tuple(range(1, F_SEQUENCE + 1)):
            raise EnrollmentNotificationAuditQualificationError(
                "F historical manifest prefix was renumbered"
            )
        e_row = result[E_SEQUENCE - 1]
        if e_row.get("migration_id") != E_MIGRATION_ID or int(
            e_row.get("sequence_number", -1)
        ) != E_SEQUENCE:
            raise EnrollmentNotificationAuditQualificationError(
                "F requires immutable E migration at sequence 34"
            )
        row = result[F_SEQUENCE - 1]
        expected = {
            "migration_id": F_MIGRATION_ID,
            "milestone_id": F_MILESTONE_ID,
            "sequence_number": F_SEQUENCE,
            "forward_file": F_FORWARD_FILE,
            "rollback_file": F_ROLLBACK_FILE,
            "depends_on": [F_DEPENDENCY],
            "transaction_policy": "embedded",
            "destructive": False,
        }
        for key, value in expected.items():
            if row.get(key) != value:
                raise EnrollmentNotificationAuditQualificationError(
                    f"F manifest row mismatch: {key}"
                )
        return result

    @classmethod
    def verify_repository_artifacts(
        cls, repository_root: Path
    ) -> tuple[dict[str, object], ...]:
        root = Path(repository_root)
        rows = cls._read_manifest(root / "database/migrations/migration_manifest.json")
        row = rows[F_SEQUENCE - 1]
        for filename, hash_key, size_key in (
            (F_FORWARD_FILE, "forward_sha256", "forward_byte_size"),
            (F_ROLLBACK_FILE, "rollback_sha256", "rollback_byte_size"),
        ):
            path = root / "database/migrations" / filename
            if not path.is_file():
                raise EnrollmentNotificationAuditQualificationError(
                    f"missing F migration artifact: {filename}"
                )
            raw = path.read_bytes()
            if row.get(hash_key) != sha256(raw).hexdigest():
                raise EnrollmentNotificationAuditQualificationError(
                    f"F migration checksum mismatch: {filename}"
                )
            if int(row.get(size_key, -1)) != len(raw):
                raise EnrollmentNotificationAuditQualificationError(
                    f"F migration byte-size mismatch: {filename}"
                )
        return rows

    @staticmethod
    def _assert_ledger(
        manifest_rows: tuple[dict[str, object], ...],
        ledger_rows: list[tuple[Any, ...]],
        *,
        minimum_count: int,
        exact_count: int | None = None,
    ) -> None:
        if exact_count is not None and len(ledger_rows) != exact_count:
            raise EnrollmentNotificationAuditQualificationError(
                f"database migration ledger count is {len(ledger_rows)}, expected {exact_count}"
            )
        if len(ledger_rows) < minimum_count:
            raise EnrollmentNotificationAuditQualificationError(
                f"database migration ledger count is {len(ledger_rows)}, expected at least {minimum_count}"
            )
        if len(ledger_rows) > len(manifest_rows):
            raise EnrollmentNotificationAuditQualificationError(
                "database migration ledger contains migrations unknown to the repository"
            )
        for manifest, ledger in zip(manifest_rows[: len(ledger_rows)], ledger_rows):
            migration_id, sequence_number, checksum_sha256, status = ledger
            if str(migration_id) != str(manifest.get("migration_id")):
                raise EnrollmentNotificationAuditQualificationError(
                    "migration ledger contains an unknown/missing migration"
                )
            if int(sequence_number) != int(manifest.get("sequence_number", -1)):
                raise EnrollmentNotificationAuditQualificationError(
                    "migration ledger sequence mismatch"
                )
            if str(checksum_sha256) != str(manifest.get("forward_sha256")):
                raise EnrollmentNotificationAuditQualificationError(
                    f"migration checksum mismatch: {migration_id}"
                )
            if str(status) != "APPLIED":
                raise EnrollmentNotificationAuditQualificationError(
                    f"migration is not APPLIED: {migration_id} ({status})"
                )

    @staticmethod
    def _auth_tables(cursor: Any) -> tuple[str, ...]:
        cursor.execute(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'nexilabs_auth' AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
        return tuple(str(row[0]) for row in cursor.fetchall())

    @staticmethod
    def _count(cursor: Any, table: str) -> int:
        cursor.execute(f"SELECT COUNT(*) FROM nexilabs_auth.{table}")
        return int(cursor.fetchone()[0])

    @staticmethod
    def _assert_f_structure(cursor: Any) -> None:
        for table, required in REQUIRED_F_COLUMNS:
            cursor.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'nexilabs_auth' AND table_name = %s
                """,
                (table,),
            )
            present = {str(row[0]) for row in cursor.fetchall()}
            missing = sorted(required - present)
            if missing:
                raise EnrollmentNotificationAuditQualificationError(
                    f"missing F columns on {table}: {', '.join(missing)}"
                )

        cursor.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'nexilabs_auth'")
        indexes = {str(row[0]) for row in cursor.fetchall()}
        missing_indexes = sorted(REQUIRED_F_INDEXES - indexes)
        if missing_indexes:
            raise EnrollmentNotificationAuditQualificationError(
                f"missing F indexes: {', '.join(missing_indexes)}"
            )

        cursor.execute(
            """
            SELECT constraint_name FROM information_schema.table_constraints
            WHERE table_schema = 'nexilabs_auth'
            """
        )
        constraints = {str(row[0]) for row in cursor.fetchall()}
        missing_constraints = sorted(REQUIRED_F_CONSTRAINTS - constraints)
        if missing_constraints:
            raise EnrollmentNotificationAuditQualificationError(
                f"missing F constraints: {', '.join(missing_constraints)}"
            )

        cursor.execute(
            """
            SELECT routine_name FROM information_schema.routines
            WHERE routine_schema = 'nexilabs_auth'
            """
        )
        functions = {str(row[0]) for row in cursor.fetchall()}
        missing_functions = sorted(REQUIRED_F_FUNCTIONS - functions)
        if missing_functions:
            raise EnrollmentNotificationAuditQualificationError(
                f"missing F functions: {', '.join(missing_functions)}"
            )

        cursor.execute(
            """
            SELECT trigger_name FROM information_schema.triggers
            WHERE trigger_schema = 'nexilabs_auth'
            """
        )
        triggers = {str(row[0]) for row in cursor.fetchall()}
        missing_triggers = sorted(REQUIRED_F_TRIGGERS - triggers)
        if missing_triggers:
            raise EnrollmentNotificationAuditQualificationError(
                f"missing F triggers: {', '.join(missing_triggers)}"
            )

    @staticmethod
    def _predecessor_operational_counts(report: Any) -> dict[str, int]:
        return {
            "principal": int(report.principal_count),
            "credential": int(report.credential_count),
            "developer_request": int(report.developer_request_count),
            "admin_operator": int(report.admin_operator_count),
            "developer_decision": int(report.developer_decision_count),
            "email_challenge": int(report.email_challenge_count),
            "enigma_profile": int(report.enigma_profile_count),
            "principal_enigma_profile": int(report.principal_enigma_profile_count),
            "bundle": int(report.bundle_count),
            "bundle_secret": int(report.bundle_secret_count),
            "delivery": int(report.delivery_count),
        }

    def _inspect_database(
        self,
        *,
        manifest_rows: tuple[dict[str, object], ...],
        predecessor_report: Any,
        expected_database: str,
        phase: str,
    ) -> EnrollmentNotificationAuditQualificationReport:
        pre_f = phase == "pre-F"
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database()")
                database_name = str(cursor.fetchone()[0])
                if database_name != expected_database:
                    raise EnrollmentNotificationAuditQualificationError(
                        f"wrong database target: expected {expected_database}, got {database_name}"
                    )
                cursor.execute(
                    "SELECT COALESCE((SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()), FALSE)"
                )
                tls_active = bool(cursor.fetchone()[0])
                if not tls_active:
                    raise EnrollmentNotificationAuditQualificationError(
                        "PostgreSQL TLS is not active"
                    )
                cursor.execute(
                    """
                    SELECT migration_id, sequence_number, checksum_sha256, status
                    FROM platform.schema_migration ORDER BY sequence_number
                    """
                )
                ledger_rows = list(cursor.fetchall())
                if pre_f:
                    self._assert_ledger(
                        manifest_rows,
                        ledger_rows,
                        minimum_count=E_SEQUENCE,
                        exact_count=E_SEQUENCE,
                    )
                else:
                    self._assert_ledger(
                        manifest_rows, ledger_rows, minimum_count=F_SEQUENCE
                    )

                auth_tables = self._auth_tables(cursor)
                if pre_f:
                    if set(auth_tables) != set(POST_E_AUTH_TABLES):
                        raise EnrollmentNotificationAuditQualificationError(
                            "F preflight requires the exact governed post-E auth table set"
                        )
                    f_counts = {
                        "enrollment_event": 0,
                        "notification_delivery": 0,
                        "audit_export": 0,
                    }
                else:
                    missing_tables = set(POST_F_AUTH_TABLES) - set(auth_tables)
                    if missing_tables:
                        raise EnrollmentNotificationAuditQualificationError(
                            "nexilabs_auth is missing F enrollment/notification/audit tables"
                        )
                    self._assert_f_structure(cursor)
                    f_counts = {
                        "enrollment_event": self._count(cursor, "enrollment_event"),
                        "notification_delivery": self._count(cursor, "notification_delivery"),
                        "audit_export": self._count(cursor, "audit_export"),
                    }

                predecessor_counts = self._predecessor_operational_counts(predecessor_report)
                is_f_tail = not pre_f and len(ledger_rows) == F_SEQUENCE
                if pre_f or is_f_tail:
                    all_counts = {**predecessor_counts, **f_counts}
                    nonzero = {name: value for name, value in all_counts.items() if value != 0}
                    if nonzero:
                        raise EnrollmentNotificationAuditQualificationError(
                            "F persistence closure requires zero operational authority rows: "
                            + ", ".join(f"{k}={v}" for k, v in sorted(nonzero.items()))
                        )

                tail_sequence = int(ledger_rows[-1][1]) if ledger_rows else 0
                tail_id = str(ledger_rows[-1][0]) if ledger_rows else ""
                return EnrollmentNotificationAuditQualificationReport(
                    phase=phase,
                    database_name=database_name,
                    tls_active=tls_active,
                    repository_migration_count=len(manifest_rows),
                    database_migration_count=len(ledger_rows),
                    migration_tail_sequence=tail_sequence,
                    migration_tail_id=tail_id,
                    nexilabs_auth_tables=auth_tables,
                    public_schema_privilege_count=int(predecessor_report.public_schema_privilege_count),
                    public_table_privilege_count=int(predecessor_report.public_table_privilege_count),
                    public_routine_privilege_count=int(predecessor_report.public_routine_privilege_count),
                    principal_count=predecessor_counts["principal"],
                    credential_count=predecessor_counts["credential"],
                    developer_request_count=predecessor_counts["developer_request"],
                    admin_operator_count=predecessor_counts["admin_operator"],
                    developer_decision_count=predecessor_counts["developer_decision"],
                    email_challenge_count=predecessor_counts["email_challenge"],
                    enigma_catalogue_count=int(predecessor_report.enigma_catalogue_count),
                    enigma_catalogue_entry_count=int(predecessor_report.enigma_catalogue_entry_count),
                    enigma_profile_count=predecessor_counts["enigma_profile"],
                    principal_enigma_profile_count=predecessor_counts["principal_enigma_profile"],
                    bundle_count=predecessor_counts["bundle"],
                    bundle_secret_count=predecessor_counts["bundle_secret"],
                    delivery_count=predecessor_counts["delivery"],
                    enrollment_event_count=f_counts["enrollment_event"],
                    notification_delivery_count=f_counts["notification_delivery"],
                    audit_export_count=f_counts["audit_export"],
                )

    def preflight(
        self, *, repository_root: Path, expected_database: str = "npp_dev"
    ) -> EnrollmentNotificationAuditQualificationReport:
        rows = self.verify_repository_artifacts(repository_root)
        predecessor = PostgreSQLCredentialBundleQualification(self.pool).verify(
            repository_root=repository_root,
            expected_database=expected_database,
        )
        if predecessor.database_migration_count != E_SEQUENCE or (
            predecessor.migration_tail_sequence != E_SEQUENCE
            or predecessor.migration_tail_id != E_MIGRATION_ID
        ):
            raise EnrollmentNotificationAuditQualificationError(
                "F preflight requires exact E database tail at sequence 34"
            )
        return self._inspect_database(
            manifest_rows=rows,
            predecessor_report=predecessor,
            expected_database=expected_database,
            phase="pre-F",
        )

    def verify(
        self, *, repository_root: Path, expected_database: str = "npp_dev"
    ) -> EnrollmentNotificationAuditQualificationReport:
        rows = self.verify_repository_artifacts(repository_root)
        predecessor = PostgreSQLCredentialBundleQualification(self.pool).verify(
            repository_root=repository_root,
            expected_database=expected_database,
        )
        return self._inspect_database(
            manifest_rows=rows,
            predecessor_report=predecessor,
            expected_database=expected_database,
            phase="post-F",
        )

    def qualify_adapter(self) -> EnrollmentNotificationAuditAdapterQualificationReceipt:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=30)
        retention = now + timedelta(days=30)

        admin_principal = "principal:qualification:p006-ui-10-2-f:admin"
        admin_email = "email:qualification:p006-ui-10-2-f:admin"
        admin_operator = "admin-operator:qualification:p006-ui-10-2-f"
        request_id = "developer-request:qualification:p006-ui-10-2-f:approved"
        rejected_request_id = "developer-request:qualification:p006-ui-10-2-f:rejected"
        decision_id = "developer-decision:qualification:p006-ui-10-2-f:approved"
        rejected_decision_id = "developer-decision:qualification:p006-ui-10-2-f:rejected"
        developer_principal = "principal:qualification:p006-ui-10-2-f:developer"
        developer_email = "email:qualification:p006-ui-10-2-f:developer"
        setup_id = "developer-setup:qualification:p006-ui-10-2-f"
        challenge_id = "email-challenge:qualification:p006-ui-10-2-f"
        profile_id = "enigma-profile:qualification:p006-ui-10-2-f"
        assignment_id = "enigma-assignment:qualification:p006-ui-10-2-f"
        bundle_id = "bundle:qualification:p006-ui-10-2-f"
        delivery_id = "delivery:qualification:p006-ui-10-2-f"
        notification_id = "notification:qualification:p006-ui-10-2-f:admin-alert"
        failed_notification_id = "notification:qualification:p006-ui-10-2-f:failed"
        export_id = "audit-export:qualification:p006-ui-10-2-f"

        events: list[tuple[str, str, str, str, str | None]] = []

        def add_event(
            cursor: Any,
            suffix: str,
            event_type: str,
            authority_type: str,
            authority_id: str,
            causation: str | None,
        ) -> str:
            event_id = f"event:qualification:p006-ui-10-2-f:{suffix}"
            cursor.execute(
                """
                INSERT INTO nexilabs_auth.enrollment_event (
                    event_id, request_id, event_type, authority_type, authority_id,
                    occurred_at, source_reference, correlation_id, causation_event_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event_id,
                    request_id if event_type != "REJECTED" else rejected_request_id,
                    event_type,
                    authority_type,
                    authority_id,
                    now,
                    f"receipt:qualification:p006-ui-10-2-f:{suffix}",
                    "correlation:qualification:p006-ui-10-2-f",
                    causation,
                ),
            )
            events.append((event_id, event_type, authority_type, authority_id, causation))
            return event_id

        with self.pool.connection(read_only=False) as connection:
            try:
                with connection.transaction():
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.principal_account (
                                principal_id, username, username_key, identity_type, account_state
                            ) VALUES (%s, 'qualification_f_admin', 'qualification_f_admin',
                                      'nexadevs_developer', 'ACTIVE')
                            """,
                            (admin_principal,),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.account_email (
                                email_id, principal_id, email_address, email_key,
                                verification_state, is_primary, verified_at
                            ) VALUES (%s, %s, 'qualification-f-admin@example.invalid',
                                      'qualification-f-admin@example.invalid', 'VERIFIED', TRUE, %s)
                            """,
                            (admin_email, admin_principal, now),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.admin_operator (
                                admin_operator_id, principal_id, admin_developer_id,
                                admin_developer_id_key, bound_admin_email_id,
                                admin_state, audit_reference
                            ) VALUES (%s, %s, 'QUALIFICATION-F-ADMIN',
                                      'qualification-f-admin', %s, 'ACTIVE',
                                      'audit:qualification:p006-ui-10-2-f')
                            """,
                            (admin_operator, admin_principal, admin_email),
                        )

                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.developer_access_request (
                                request_id, first_name, last_name, email_address,
                                email_key, request_state
                            ) VALUES (%s, 'Qualification', 'Developer',
                                      'qualification-f-developer@example.invalid',
                                      'qualification-f-developer@example.invalid', 'SUBMITTED')
                            """,
                            (request_id,),
                        )
                        previous = add_event(
                            cursor, "request-received", "REQUEST_RECEIVED",
                            "DEVELOPER_ACCESS_REQUEST", request_id, None,
                        )
                        cursor.execute(
                            "UPDATE nexilabs_auth.developer_access_request SET request_state='UNDER_REVIEW' WHERE request_id=%s",
                            (request_id,),
                        )
                        previous = add_event(
                            cursor, "under-review", "UNDER_REVIEW",
                            "DEVELOPER_ACCESS_REQUEST", request_id, previous,
                        )

                        receipt = "receipt:qualification:p006-ui-10-2-f:approved"
                        cursor.execute("SET CONSTRAINTS ALL DEFERRED")
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.developer_access_decision (
                                decision_id, request_id, reviewer_principal_id, admin_operator_id,
                                decision, reason_code, safe_explanation, internal_reference,
                                policy_version, receipt_reference, decided_at
                            ) VALUES (%s, %s, %s, %s, 'APPROVED', NULL, NULL,
                                      'internal:qualification:p006-ui-10-2-f:approved',
                                      'qualification-policy-v1', %s, %s)
                            """,
                            (decision_id, request_id, admin_principal, admin_operator, receipt, now),
                        )
                        cursor.execute(
                            """
                            UPDATE nexilabs_auth.developer_access_request
                            SET request_state='APPROVED', decided_at=%s,
                                decision_reference=%s, terminal_decision_id=%s
                            WHERE request_id=%s
                            """,
                            (now, receipt, decision_id, request_id),
                        )
                        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
                        previous = add_event(
                            cursor, "approved", "APPROVED",
                            "DEVELOPER_ACCESS_DECISION", decision_id, previous,
                        )

                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.principal_account (
                                principal_id, username, username_key, identity_type, account_state
                            ) VALUES (%s, 'qualification_f_developer', 'qualification_f_developer',
                                      'nexadevs_developer', 'PENDING')
                            """,
                            (developer_principal,),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.account_email (
                                email_id, principal_id, email_address, email_key,
                                verification_state, is_primary, verification_requested_at,
                                verification_reference
                            ) VALUES (%s, %s, 'qualification-f-developer@example.invalid',
                                      'qualification-f-developer@example.invalid', 'PENDING', TRUE,
                                      %s, 'verification:qualification:p006-ui-10-2-f')
                            """,
                            (developer_email, developer_principal, now),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.developer_setup (
                                developer_setup_id, request_id, setup_lookup_key,
                                setup_secret_verifier_scheme, setup_secret_verifier_version,
                                setup_secret_verifier_payload, setup_state, issued_at, expires_at,
                                issuance_reference
                            ) VALUES (%s, %s, %s, 'qualification-hmac', 1, %s,
                                      'ISSUED', %s, %s, 'issuance:qualification:p006-ui-10-2-f')
                            """,
                            (
                                setup_id,
                                request_id,
                                "qualification-f-setup-lookup-key-0001",
                                "opaque-setup-secret-verifier-qualification-f",
                                now,
                                expires,
                            ),
                        )
                        previous = add_event(
                            cursor, "setup-issued", "SETUP_ISSUED",
                            "DEVELOPER_SETUP", setup_id, previous,
                        )
                        cursor.execute(
                            """
                            UPDATE nexilabs_auth.developer_setup
                            SET setup_state='CONSUMED', consumed_at=%s, resulting_principal_id=%s
                            WHERE developer_setup_id=%s
                            """,
                            (now, developer_principal, setup_id),
                        )
                        previous = add_event(
                            cursor, "setup-verified", "SETUP_VERIFIED",
                            "DEVELOPER_SETUP", setup_id, previous,
                        )

                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.email_verification_challenge (
                                challenge_id, principal_id, email_id, otp_verifier_scheme,
                                otp_verifier_version, otp_verifier_payload, challenge_state,
                                policy_version, issued_at, expires_at, max_attempts
                            ) VALUES (%s, %s, %s, 'qualification-hmac', 1, %s,
                                      'ISSUED', 'qualification-otp-policy-v1', %s, %s, 5)
                            """,
                            (
                                challenge_id,
                                developer_principal,
                                developer_email,
                                "opaque-otp-verifier-payload-qualification-f",
                                now,
                                expires,
                            ),
                        )
                        previous = add_event(
                            cursor, "otp-issued", "OTP_ISSUED",
                            "EMAIL_VERIFICATION_CHALLENGE", challenge_id, previous,
                        )
                        cursor.execute(
                            """
                            UPDATE nexilabs_auth.email_verification_challenge
                            SET challenge_state='VERIFIED', consumed_at=%s
                            WHERE challenge_id=%s
                            """,
                            (now, challenge_id),
                        )
                        cursor.execute(
                            """
                            UPDATE nexilabs_auth.account_email
                            SET verification_state='VERIFIED', verified_at=%s
                            WHERE email_id=%s
                            """,
                            (now, developer_email),
                        )
                        previous = add_event(
                            cursor, "email-verified", "EMAIL_VERIFIED",
                            "EMAIL_VERIFICATION_CHALLENGE", challenge_id, previous,
                        )

                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.enigma_profile (
                                profile_id, profile_state, created_at, activated_at, profile_reference
                            ) VALUES (%s, 'ACTIVE', %s, %s, 'qualification-f-profile')
                            """,
                            (profile_id, now, now),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.principal_enigma_profile (
                                assignment_id, principal_id, profile_id, assignment_state, assigned_at
                            ) VALUES (%s, %s, %s, 'ACTIVE', %s)
                            """,
                            (assignment_id, developer_principal, profile_id, now),
                        )
                        previous = add_event(
                            cursor, "enigma-provisioned", "ENIGMA_PROVISIONED",
                            "PRINCIPAL_ENIGMA_PROFILE", assignment_id, previous,
                        )

                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.credential_bundle (
                                bundle_id, principal_id, enigma_profile_id, bundle_state,
                                object_provider_code, object_key, content_sha256, byte_size,
                                created_at, expires_at, retention_until
                            ) VALUES (%s, %s, %s, 'GENERATED', 'QUALIFICATION_PRIVATE_OBJECT',
                                      %s, %s, 4096, %s, %s, %s)
                            """,
                            (
                                bundle_id,
                                developer_principal,
                                profile_id,
                                "qualification/private/bundle-f.zip",
                                "a" * 64,
                                now,
                                expires,
                                retention,
                            ),
                        )
                        cursor.execute(
                            """
                            UPDATE nexilabs_auth.credential_bundle
                            SET integrity_verified_at=%s, object_confirmed_at=%s,
                                ready_at=%s, bundle_state='READY'
                            WHERE bundle_id=%s
                            """,
                            (now, now, now, bundle_id),
                        )
                        previous = add_event(
                            cursor, "bundle-ready", "BUNDLE_READY",
                            "CREDENTIAL_BUNDLE", bundle_id, previous,
                        )

                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.credential_delivery (
                                delivery_id, bundle_id, token_verifier_scheme,
                                token_verifier_version, token_verifier_payload,
                                delivery_state, policy_version, logical_delivery_host_code,
                                issued_at, expires_at, download_count
                            ) VALUES (%s, %s, 'qualification-keyed-v1', 1, %s, 'ISSUED',
                                      'qualification-policy-v1', 'CREDENTIAL_DELIVERY_QUALIFICATION',
                                      %s, %s, 0)
                            """,
                            (
                                delivery_id,
                                bundle_id,
                                "opaque-delivery-token-verifier-qualification-f",
                                now,
                                expires,
                            ),
                        )
                        previous = add_event(
                            cursor, "delivery-issued", "DELIVERY_ISSUED",
                            "CREDENTIAL_DELIVERY", delivery_id, previous,
                        )

                        cursor.execute(
                            """
                            UPDATE nexilabs_auth.principal_account
                            SET account_state='ACTIVE', updated_at=CURRENT_TIMESTAMP
                            WHERE principal_id=%s
                            """,
                            (developer_principal,),
                        )
                        previous = add_event(
                            cursor, "account-activated", "ACCOUNT_ACTIVATED",
                            "PRINCIPAL_ACCOUNT", developer_principal, previous,
                        )

                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.developer_access_request (
                                request_id, first_name, last_name, email_address, email_key,
                                request_state
                            ) VALUES (%s, 'Qualification', 'Rejected',
                                      'qualification-f-rejected@example.invalid',
                                      'qualification-f-rejected@example.invalid', 'UNDER_REVIEW')
                            """,
                            (rejected_request_id,),
                        )
                        rejected_receipt = "receipt:qualification:p006-ui-10-2-f:rejected"
                        cursor.execute("SET CONSTRAINTS ALL DEFERRED")
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.developer_access_decision (
                                decision_id, request_id, reviewer_principal_id, admin_operator_id,
                                decision, reason_code, safe_explanation, internal_reference,
                                policy_version, receipt_reference, decided_at
                            ) VALUES (%s, %s, %s, %s, 'REJECTED', 'REQUEST_INCOMPLETE',
                                      'Qualification rejection',
                                      'internal:qualification:p006-ui-10-2-f:rejected',
                                      'qualification-policy-v1', %s, %s)
                            """,
                            (
                                rejected_decision_id,
                                rejected_request_id,
                                admin_principal,
                                admin_operator,
                                rejected_receipt,
                                now,
                            ),
                        )
                        cursor.execute(
                            """
                            UPDATE nexilabs_auth.developer_access_request
                            SET request_state='REJECTED', decided_at=%s,
                                decision_reference=%s, terminal_decision_id=%s
                            WHERE request_id=%s
                            """,
                            (now, rejected_receipt, rejected_decision_id, rejected_request_id),
                        )
                        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
                        add_event(
                            cursor, "rejected", "REJECTED",
                            "DEVELOPER_ACCESS_DECISION", rejected_decision_id, None,
                        )

                        request_received_event = events[0][0]
                        approved_event = next(row[0] for row in events if row[1] == "APPROVED")
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.notification_delivery (
                                notification_id, event_id, template_code, template_version,
                                recipient_reference, delivery_state, queued_at
                            ) VALUES (%s, %s, 'ADMIN_DEVELOPER_REQUEST_ALERT', 1,
                                      %s, 'QUEUED', %s)
                            """,
                            (
                                notification_id,
                                request_received_event,
                                ADMIN_OPERATIONS_RECIPIENT_REFERENCE,
                                now,
                            ),
                        )
                        cursor.execute(
                            """
                            UPDATE nexilabs_auth.notification_delivery
                            SET provider_message_reference='provider-message:qualification-f',
                                delivery_state='SENT', sent_at=%s
                            WHERE notification_id=%s
                            """,
                            (now, notification_id),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.notification_delivery (
                                notification_id, event_id, template_code, template_version,
                                recipient_reference, delivery_state, queued_at
                            ) VALUES (%s, %s, 'DEVELOPER_REQUEST_APPROVED', 1,
                                      %s, 'QUEUED', %s)
                            """,
                            (
                                failed_notification_id,
                                approved_event,
                                f"DEVELOPER_ACCESS_REQUEST:{request_id}",
                                now,
                            ),
                        )
                        cursor.execute(
                            """
                            UPDATE nexilabs_auth.notification_delivery
                            SET delivery_state='FAILED', failed_at=%s,
                                failure_code='QUALIFICATION_PROVIDER_FAILURE'
                            WHERE notification_id=%s
                            """,
                            (now, failed_notification_id),
                        )

                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.audit_export (
                                export_id, requested_by_admin_operator_id, report_type,
                                filter_reference, object_provider_code, object_key,
                                content_sha256, byte_size, export_state, generated_at,
                                expires_at, retention_until
                            ) VALUES (%s, %s, 'DEVELOPER_ENROLLMENT_AUDIT',
                                      'AUDIT_FILTER:qualification-f',
                                      'QUALIFICATION_PRIVATE_OBJECT', %s, %s, 8192,
                                      'AVAILABLE', %s, %s, %s)
                            """,
                            (
                                export_id,
                                admin_operator,
                                "qualification/private/audit-f.pdf",
                                "b" * 64,
                                now,
                                expires,
                                retention,
                            ),
                        )

                    authority = PostgreSQLEnrollmentNotificationAuditAuthority(
                        _BorrowedConnectionPool(connection)
                    )
                    event_rows = authority.events_for_request(request_id)
                    admin_alert = authority.notification_by_id(notification_id)
                    failed_alert = authority.notification_by_id(failed_notification_id)
                    audit = authority.audit_export_by_id(export_id)
                    if len(event_rows) != 11:
                        raise EnrollmentNotificationAuditQualificationError(
                            "F adapter proof approved lifecycle event count mismatch"
                        )
                    if admin_alert is None or admin_alert.delivery_state != "SENT":
                        raise EnrollmentNotificationAuditQualificationError(
                            "F adapter proof Admin alert read-back mismatch"
                        )
                    if admin_alert.recipient_reference != ADMIN_OPERATIONS_RECIPIENT_REFERENCE:
                        raise EnrollmentNotificationAuditQualificationError(
                            "F adapter proof Admin alert recipient minimization mismatch"
                        )
                    if failed_alert is None or failed_alert.delivery_state != "FAILED":
                        raise EnrollmentNotificationAuditQualificationError(
                            "F adapter proof failed-notification lifecycle mismatch"
                        )
                    if audit is None or audit.export_state != "AVAILABLE":
                        raise EnrollmentNotificationAuditQualificationError(
                            "F adapter proof audit export read-back mismatch"
                        )

                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            UPDATE nexilabs_auth.audit_export
                            SET export_state='EXPIRED', expired_at=%s
                            WHERE export_id=%s
                            """,
                            (expires, export_id),
                        )
                        cursor.execute(
                            """
                            UPDATE nexilabs_auth.audit_export
                            SET export_state='RETIRED', retired_at=%s
                            WHERE export_id=%s
                            """,
                            (retention, export_id),
                        )
                    terminal_audit = authority.audit_export_by_id(export_id)
                    if terminal_audit is None or terminal_audit.export_state != "RETIRED":
                        raise EnrollmentNotificationAuditQualificationError(
                            "F adapter proof audit retention lifecycle mismatch"
                        )
                    raise _ProofRollback()
            except _ProofRollback:
                pass

            checks: list[int] = []
            with connection.cursor() as cursor:
                for table, column, value in (
                    ("enrollment_event", "request_id", request_id),
                    ("enrollment_event", "request_id", rejected_request_id),
                    ("notification_delivery", "notification_id", notification_id),
                    ("notification_delivery", "notification_id", failed_notification_id),
                    ("audit_export", "export_id", export_id),
                    ("credential_delivery", "delivery_id", delivery_id),
                    ("credential_bundle", "bundle_id", bundle_id),
                    ("email_verification_challenge", "challenge_id", challenge_id),
                    ("developer_access_decision", "decision_id", decision_id),
                    ("developer_access_decision", "decision_id", rejected_decision_id),
                    ("developer_access_request", "request_id", request_id),
                    ("developer_access_request", "request_id", rejected_request_id),
                    ("admin_operator", "admin_operator_id", admin_operator),
                    ("principal_account", "principal_id", admin_principal),
                    ("principal_account", "principal_id", developer_principal),
                ):
                    cursor.execute(
                        f"SELECT COUNT(*) FROM nexilabs_auth.{table} WHERE {column} = %s",
                        (value,),
                    )
                    checks.append(int(cursor.fetchone()[0]))
        if any(checks):
            raise EnrollmentNotificationAuditQualificationError(
                "F adapter proof did not fully roll back synthetic authority"
            )
        return EnrollmentNotificationAuditAdapterQualificationReceipt(
            request_id=request_id,
            event_count=len(events),
            notification_id=notification_id,
            admin_alert_recipient_reference=ADMIN_OPERATIONS_RECIPIENT_REFERENCE,
            audit_export_id=export_id,
            notification_state="SENT",
            audit_export_state="RETIRED",
            rollback_verified=True,
        )


__all__ = [
    "F_CATALOGUE_VERSION",
    "F_DEPENDENCY",
    "F_FORWARD_FILE",
    "F_MIGRATION_ID",
    "F_MILESTONE_ID",
    "F_ROLLBACK_FILE",
    "F_SEQUENCE",
    "POST_F_AUTH_TABLES",
    "PostgreSQLEnrollmentNotificationAuditQualification",
    "REQUIRED_F_COLUMNS",
    "REQUIRED_F_CONSTRAINTS",
    "REQUIRED_F_FUNCTIONS",
    "REQUIRED_F_INDEXES",
    "REQUIRED_F_TRIGGERS",
]
