"""P006.UI.10.2.C — PostgreSQL structural, ledger, ACL and adapter qualification."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .contracts import (
    ADMIN_PASSWORD_KIND,
    AdminReviewAdapterQualificationReceipt,
    AdminReviewQualificationError,
    AdminReviewQualificationReport,
)
from .postgresql import PostgreSQLAdminReviewAuthority


C_MIGRATION_ID = "m006_10_02_layered_admin_review_authority"
C_MILESTONE_ID = "M006.10.2"
C_SEQUENCE = 32
C_CATALOGUE_VERSION = 16
C_FORWARD_FILE = f"{C_MIGRATION_ID}.sql"
C_ROLLBACK_FILE = f"{C_MIGRATION_ID}_rollback.sql"
C_DEPENDENCY = "m006_10_02_nexilabs_account_credential_authority"

PRE_C_AUTH_TABLES = (
    "account_email",
    "credential_verifier",
    "developer_access_request",
    "developer_setup",
    "enigma_catalogue",
    "enigma_catalogue_entry",
    "enigma_profile",
    "enigma_profile_catalogue",
    "principal_account",
    "principal_enigma_profile",
    "principal_permission",
    "principal_profile",
)
POST_C_AUTH_TABLES = tuple(sorted((*PRE_C_AUTH_TABLES, "admin_operator", "developer_access_decision")))

REQUIRED_C_INDEXES = frozenset(
    {
        "ux_nexilabs_auth_admin_developer_id",
        "ux_nexilabs_auth_admin_developer_id_key",
        "ux_nexilabs_auth_active_admin_operator_principal",
        "ix_nexilabs_auth_admin_operator_state",
        "ix_nexilabs_auth_admin_operator_email",
        "ux_nexilabs_auth_active_admin_password",
        "ix_nexilabs_auth_developer_decision_reviewer",
        "ix_nexilabs_auth_developer_decision_admin_operator",
        "ix_nexilabs_auth_developer_decision_decided",
    }
)
REQUIRED_C_CONSTRAINTS = frozenset(
    {
        "uq_nexilabs_auth_email_id_principal",
        "uq_nexilabs_auth_admin_operator_id_principal",
        "fk_nexilabs_auth_admin_operator_email_owner",
        "ck_nexilabs_auth_admin_operator_id_nonblank",
        "ck_nexilabs_auth_admin_developer_id_nonblank",
        "ck_nexilabs_auth_admin_developer_id_key_canonical",
        "ck_nexilabs_auth_admin_operator_state_time",
        "ck_nexilabs_auth_admin_bootstrap_reference_nonblank",
        "ck_nexilabs_auth_admin_audit_reference_nonblank",
        "uq_nexilabs_auth_request_terminal_projection",
        "uq_nexilabs_auth_developer_decision_request",
        "uq_nexilabs_auth_developer_decision_projection",
        "fk_nexilabs_auth_developer_decision_request",
        "fk_nexilabs_auth_developer_decision_reviewer_operator",
        "fk_nexilabs_auth_decision_request_projection",
        "ck_nexilabs_auth_developer_decision_id_nonblank",
        "ck_nexilabs_auth_developer_decision_reason",
        "ck_nexilabs_auth_developer_decision_safe_explanation",
        "ck_nexilabs_auth_developer_decision_internal_reference",
        "ck_nexilabs_auth_developer_decision_policy_version",
        "ck_nexilabs_auth_developer_decision_receipt_reference",
        "ck_nexilabs_auth_request_terminal_decision_presence",
        "fk_nexilabs_auth_request_terminal_decision",
    }
)
REQUIRED_C_FUNCTIONS = frozenset(
    {
        "validate_admin_operator_binding",
        "reject_developer_access_decision_mutation",
        "validate_developer_access_decision_reviewer",
    }
)
REQUIRED_C_TRIGGERS = frozenset(
    {
        "tr_nexilabs_auth_admin_operator_binding",
        "tr_nexilabs_auth_developer_access_decision_immutable",
        "tr_nexilabs_auth_developer_access_decision_reviewer",
    }
)
REQUIRED_C_COLUMNS = {
    "admin_operator": frozenset(
        {
            "admin_operator_id",
            "principal_id",
            "admin_developer_id",
            "admin_developer_id_key",
            "bound_admin_email_id",
            "admin_state",
            "created_at",
            "disabled_at",
            "bootstrap_reference",
            "audit_reference",
        }
    ),
    "developer_access_decision": frozenset(
        {
            "decision_id",
            "request_id",
            "reviewer_principal_id",
            "admin_operator_id",
            "decision",
            "reason_code",
            "safe_explanation",
            "internal_reference",
            "policy_version",
            "receipt_reference",
            "decided_at",
        }
    ),
    "developer_access_request": frozenset({"terminal_decision_id"}),
}

B_CATALOGUES = (
    (
        "enigma:catalogue:shared:3:v1",
        3,
        1,
        "ACTIVE",
        "development/auth/private/enigma/enigma_words_3.csv",
        "aff0a9324d273dfe5c67c9c05421308b250e56b59c5bbeb1faa1fc8764e16fa8",
    ),
    (
        "enigma:catalogue:shared:4:v1",
        4,
        1,
        "ACTIVE",
        "development/auth/private/enigma/enigma_words_4.csv",
        "481c59c836e84d797b5cd1c1633618551d8329575be542c8f426a14e088dc1a0",
    ),
    (
        "enigma:catalogue:shared:5:v1",
        5,
        1,
        "ACTIVE",
        "development/auth/private/enigma/enigma_words_5.csv",
        "ca003d38352b5b6f348000608cf7b0a6f70f8e42557735b85aaaa2d8b981fa9e",
    ),
)


class _ProofRollback(RuntimeError):
    pass


class _BorrowedConnectionPool:
    def __init__(self, connection: Any):
        self.connection_object = connection

    @contextmanager
    def connection(self, read_only: bool = False):
        yield self.connection_object


class PostgreSQLAdminReviewQualification:
    """Qualify the C migration state without creating a parallel migration runner."""

    def __init__(self, pool: Any):
        if pool is None or not callable(getattr(pool, "connection", None)):
            raise TypeError("pool with connection(read_only=...) is required")
        self.pool = pool

    @staticmethod
    def _read_manifest(manifest_path: Path) -> tuple[dict[str, object], ...]:
        try:
            payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise AdminReviewQualificationError("cannot read the live migration manifest") from exc
        if payload.get("catalogue_version") != C_CATALOGUE_VERSION:
            raise AdminReviewQualificationError(
                f"C requires migration catalogue_version {C_CATALOGUE_VERSION}"
            )
        rows = payload.get("migrations")
        if not isinstance(rows, list) or len(rows) != C_SEQUENCE:
            raise AdminReviewQualificationError("C requires exactly 32 manifest migrations")
        result = tuple(row for row in rows if isinstance(row, dict))
        if len(result) != len(rows):
            raise AdminReviewQualificationError("migration manifest contains a malformed row")
        row = result[-1]
        expected = {
            "migration_id": C_MIGRATION_ID,
            "milestone_id": C_MILESTONE_ID,
            "sequence_number": C_SEQUENCE,
            "forward_file": C_FORWARD_FILE,
            "rollback_file": C_ROLLBACK_FILE,
            "depends_on": [C_DEPENDENCY],
            "transaction_policy": "embedded",
            "destructive": False,
        }
        for key, value in expected.items():
            if row.get(key) != value:
                raise AdminReviewQualificationError(f"C manifest row mismatch: {key}")
        return result

    @classmethod
    def verify_repository_artifacts(cls, repository_root: Path) -> tuple[dict[str, object], ...]:
        root = Path(repository_root)
        manifest_path = root / "database" / "migrations" / "migration_manifest.json"
        rows = cls._read_manifest(manifest_path)
        row = rows[-1]
        for filename, hash_key, size_key in (
            (C_FORWARD_FILE, "forward_sha256", "forward_byte_size"),
            (C_ROLLBACK_FILE, "rollback_sha256", "rollback_byte_size"),
        ):
            path = root / "database" / "migrations" / filename
            if not path.is_file():
                raise AdminReviewQualificationError(f"missing C migration artifact: {filename}")
            raw = path.read_bytes()
            if row.get(hash_key) != sha256(raw).hexdigest():
                raise AdminReviewQualificationError(f"C migration checksum mismatch: {filename}")
            if int(row.get(size_key, -1)) != len(raw):
                raise AdminReviewQualificationError(f"C migration byte-size mismatch: {filename}")
        return rows

    @staticmethod
    def _assert_ledger(
        manifest_rows: tuple[dict[str, object], ...],
        ledger_rows: list[tuple[Any, ...]],
        *,
        expected_count: int,
    ) -> None:
        if len(ledger_rows) != expected_count:
            raise AdminReviewQualificationError(
                f"database migration ledger count is {len(ledger_rows)}, expected {expected_count}"
            )
        for manifest, ledger in zip(manifest_rows[:expected_count], ledger_rows):
            migration_id, sequence_number, checksum_sha256, status = ledger
            if str(migration_id) != str(manifest.get("migration_id")):
                raise AdminReviewQualificationError("migration ledger contains an unknown/missing migration")
            if int(sequence_number) != int(manifest.get("sequence_number", -1)):
                raise AdminReviewQualificationError("migration ledger sequence mismatch")
            if str(checksum_sha256) != str(manifest.get("forward_sha256")):
                raise AdminReviewQualificationError(
                    f"migration checksum mismatch: {migration_id}"
                )
            if str(status) != "APPLIED":
                raise AdminReviewQualificationError(
                    f"migration is not APPLIED: {migration_id} ({status})"
                )

    @staticmethod
    def _assert_b_catalogues(cursor: Any) -> tuple[int, int]:
        cursor.execute(
            """
            SELECT catalogue_id, word_length, catalogue_version, catalogue_state,
                   source_reference, source_sha256
            FROM nexilabs_auth.enigma_catalogue
            ORDER BY word_length
            """
        )
        actual = tuple(
            (str(a), int(b), int(c), str(d), str(e), str(f))
            for a, b, c, d, e, f in cursor.fetchall()
        )
        if actual != B_CATALOGUES:
            raise AdminReviewQualificationError("governed B Enigma catalogue metadata differs")
        cursor.execute(
            """
            SELECT word_length, COUNT(*)
            FROM nexilabs_auth.enigma_catalogue_entry
            GROUP BY word_length
            ORDER BY word_length
            """
        )
        family_counts = tuple((int(a), int(b)) for a, b in cursor.fetchall())
        if family_counts != ((3, 93), (4, 93), (5, 93)):
            raise AdminReviewQualificationError("governed B Enigma entry counts differ")
        return len(actual), sum(count for _, count in family_counts)

    @staticmethod
    def _public_privileges(cursor: Any) -> tuple[int, int, int]:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM pg_namespace AS n
            CROSS JOIN LATERAL aclexplode(
                COALESCE(n.nspacl, acldefault('n', n.nspowner))
            ) AS acl
            WHERE n.nspname = 'nexilabs_auth'
              AND acl.grantee = 0
            """
        )
        schema_count = int(cursor.fetchone()[0])
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.table_privileges
            WHERE table_schema = 'nexilabs_auth'
              AND grantee = 'PUBLIC'
            """
        )
        table_count = int(cursor.fetchone()[0])
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.routine_privileges
            WHERE routine_schema = 'nexilabs_auth'
              AND grantee = 'PUBLIC'
            """
        )
        routine_count = int(cursor.fetchone()[0])
        if schema_count or table_count or routine_count:
            raise AdminReviewQualificationError("PUBLIC privileges are present on nexilabs_auth authority")
        return schema_count, table_count, routine_count

    @staticmethod
    def _count(cursor: Any, table: str) -> int:
        cursor.execute(f"SELECT COUNT(*) FROM nexilabs_auth.{table}")
        return int(cursor.fetchone()[0])

    @classmethod
    def _closure_counts(cls, cursor: Any, *, post_c: bool) -> dict[str, int]:
        counts = {
            "principal": cls._count(cursor, "principal_account"),
            "credential": cls._count(cursor, "credential_verifier"),
            "developer_request": cls._count(cursor, "developer_access_request"),
            "enigma_profile": cls._count(cursor, "enigma_profile"),
            "principal_enigma_profile": cls._count(cursor, "principal_enigma_profile"),
        }
        if post_c:
            counts["admin_operator"] = cls._count(cursor, "admin_operator")
            counts["developer_decision"] = cls._count(cursor, "developer_access_decision")
        else:
            counts["admin_operator"] = 0
            counts["developer_decision"] = 0
        expected_zero = (
            "principal",
            "credential",
            "developer_request",
            "enigma_profile",
            "principal_enigma_profile",
            "admin_operator",
            "developer_decision",
        )
        for label in expected_zero:
            if counts[label] != 0:
                raise AdminReviewQualificationError(
                    f"C persistence closure requires zero {label} rows, found {counts[label]}"
                )
        return counts

    @staticmethod
    def _auth_tables(cursor: Any) -> tuple[str, ...]:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'nexilabs_auth'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
        return tuple(str(row[0]) for row in cursor.fetchall())

    @staticmethod
    def _assert_post_c_structure(cursor: Any) -> None:
        for table, required in REQUIRED_C_COLUMNS.items():
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'nexilabs_auth'
                  AND table_name = %s
                """,
                (table,),
            )
            present = {str(row[0]) for row in cursor.fetchall()}
            missing = sorted(required - present)
            if missing:
                raise AdminReviewQualificationError(
                    f"missing C columns on {table}: {', '.join(missing)}"
                )

        cursor.execute(
            "SELECT indexname FROM pg_indexes WHERE schemaname = 'nexilabs_auth'"
        )
        indexes = {str(row[0]) for row in cursor.fetchall()}
        missing_indexes = sorted(REQUIRED_C_INDEXES - indexes)
        if missing_indexes:
            raise AdminReviewQualificationError(
                f"missing C indexes: {', '.join(missing_indexes)}"
            )

        cursor.execute(
            """
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = 'nexilabs_auth'
            """
        )
        constraints = {str(row[0]) for row in cursor.fetchall()}
        missing_constraints = sorted(REQUIRED_C_CONSTRAINTS - constraints)
        if missing_constraints:
            raise AdminReviewQualificationError(
                f"missing C constraints: {', '.join(missing_constraints)}"
            )

        cursor.execute(
            """
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'nexilabs_auth'
            """
        )
        functions = {str(row[0]) for row in cursor.fetchall()}
        missing_functions = sorted(REQUIRED_C_FUNCTIONS - functions)
        if missing_functions:
            raise AdminReviewQualificationError(
                f"missing C functions: {', '.join(missing_functions)}"
            )

        cursor.execute(
            """
            SELECT trigger_name
            FROM information_schema.triggers
            WHERE trigger_schema = 'nexilabs_auth'
            """
        )
        triggers = {str(row[0]) for row in cursor.fetchall()}
        missing_triggers = sorted(REQUIRED_C_TRIGGERS - triggers)
        if missing_triggers:
            raise AdminReviewQualificationError(
                f"missing C triggers: {', '.join(missing_triggers)}"
            )

    def _qualify(
        self,
        *,
        repository_root: Path,
        expected_database: str,
        post_c: bool,
    ) -> AdminReviewQualificationReport:
        manifest_rows = self.verify_repository_artifacts(repository_root)
        expected_ledger_count = C_SEQUENCE if post_c else C_SEQUENCE - 1
        expected_tables = POST_C_AUTH_TABLES if post_c else PRE_C_AUTH_TABLES
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database()")
                database_name = str(cursor.fetchone()[0])
                if database_name != expected_database:
                    raise AdminReviewQualificationError(
                        f"wrong database target: expected {expected_database}, got {database_name}"
                    )

                cursor.execute(
                    "SELECT COALESCE((SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()), FALSE)"
                )
                tls_active = bool(cursor.fetchone()[0])
                if not tls_active:
                    raise AdminReviewQualificationError("PostgreSQL TLS is not active")

                cursor.execute(
                    """
                    SELECT migration_id, sequence_number, checksum_sha256, status
                    FROM platform.schema_migration
                    ORDER BY sequence_number
                    """
                )
                ledger_rows = list(cursor.fetchall())
                self._assert_ledger(
                    manifest_rows, ledger_rows, expected_count=expected_ledger_count
                )

                auth_tables = self._auth_tables(cursor)
                if auth_tables != expected_tables:
                    label = "post-C" if post_c else "pre-C"
                    raise AdminReviewQualificationError(
                        f"nexilabs_auth base-table set differs from governed {label} authority"
                    )

                schema_acl, table_acl, routine_acl = self._public_privileges(cursor)
                catalogue_count, entry_count = self._assert_b_catalogues(cursor)
                counts = self._closure_counts(cursor, post_c=post_c)
                if post_c:
                    self._assert_post_c_structure(cursor)

        return AdminReviewQualificationReport(
            phase="post-C" if post_c else "pre-C",
            database_name=database_name,
            tls_active=tls_active,
            repository_migration_count=len(manifest_rows),
            database_migration_count=len(ledger_rows),
            migration_tail_sequence=int(ledger_rows[-1][1]),
            migration_tail_id=str(ledger_rows[-1][0]),
            nexilabs_auth_tables=auth_tables,
            public_schema_privilege_count=schema_acl,
            public_table_privilege_count=table_acl,
            public_routine_privilege_count=routine_acl,
            principal_count=counts["principal"],
            credential_count=counts["credential"],
            developer_request_count=counts["developer_request"],
            admin_operator_count=counts["admin_operator"],
            developer_decision_count=counts["developer_decision"],
            enigma_catalogue_count=catalogue_count,
            enigma_catalogue_entry_count=entry_count,
            enigma_profile_count=counts["enigma_profile"],
            principal_enigma_profile_count=counts["principal_enigma_profile"],
        )

    def preflight(
        self, *, repository_root: Path, expected_database: str = "npp_dev"
    ) -> AdminReviewQualificationReport:
        return self._qualify(
            repository_root=repository_root,
            expected_database=expected_database,
            post_c=False,
        )

    def verify(
        self, *, repository_root: Path, expected_database: str = "npp_dev"
    ) -> AdminReviewQualificationReport:
        return self._qualify(
            repository_root=repository_root,
            expected_database=expected_database,
            post_c=True,
        )

    def qualify_adapter(self) -> AdminReviewAdapterQualificationReceipt:
        principal_id = "principal:qualification:p006-ui-10-2-c"
        email_id = "email:qualification:p006-ui-10-2-c"
        operator_id = "admin-operator:qualification:p006-ui-10-2-c"
        admin_developer_id = "QUALIFICATION-C-ADMIN-DEVELOPER-ID"
        request_id = "developer-request:qualification:p006-ui-10-2-c"
        decision_id = "developer-decision:qualification:p006-ui-10-2-c"
        decided_at = datetime.now(timezone.utc)
        receipt = "receipt:qualification:p006-ui-10-2-c"

        with self.pool.connection(read_only=False) as connection:
            try:
                with connection.transaction():
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.principal_account (
                                principal_id, username, username_key,
                                identity_type, account_state
                            ) VALUES (%s, %s, %s, 'nexadevs_developer', 'ACTIVE')
                            """,
                            (principal_id, "qualification_c_admin", "qualification_c_admin"),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.account_email (
                                email_id, principal_id, email_address, email_key,
                                verification_state, is_primary, verified_at
                            ) VALUES (%s, %s, %s, %s, 'VERIFIED', TRUE, %s)
                            """,
                            (
                                email_id,
                                principal_id,
                                "qualification-c-admin@example.invalid",
                                "qualification-c-admin@example.invalid",
                                decided_at,
                            ),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.credential_verifier (
                                credential_id, principal_id, credential_kind,
                                verifier_scheme, verifier_version, verifier_payload
                            ) VALUES (%s, %s, 'password', 'qualification', 1, %s)
                            """,
                            (
                                "credential:qualification:developer-password:c",
                                principal_id,
                                "qualification-developer-verifier-payload",
                            ),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.credential_verifier (
                                credential_id, principal_id, credential_kind,
                                verifier_scheme, verifier_version, verifier_payload
                            ) VALUES (%s, %s, 'ADMIN_PASSWORD', 'qualification', 1, %s)
                            """,
                            (
                                "credential:qualification:admin-password:c",
                                principal_id,
                                "qualification-admin-verifier-payload",
                            ),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.admin_operator (
                                admin_operator_id, principal_id, admin_developer_id,
                                admin_developer_id_key, bound_admin_email_id,
                                admin_state, audit_reference
                            ) VALUES (%s, %s, %s, lower(btrim(%s)), %s, 'ACTIVE', %s)
                            """,
                            (
                                operator_id,
                                principal_id,
                                admin_developer_id,
                                admin_developer_id,
                                email_id,
                                "audit:qualification:p006-ui-10-2-c",
                            ),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.developer_access_request (
                                request_id, first_name, last_name, email_address,
                                email_key, request_state
                            ) VALUES (%s, 'Qualification', 'Request', %s, %s, 'UNDER_REVIEW')
                            """,
                            (
                                request_id,
                                "qualification-request@example.invalid",
                                "qualification-request@example.invalid",
                            ),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.developer_access_decision (
                                decision_id, request_id, reviewer_principal_id,
                                admin_operator_id, decision, reason_code,
                                safe_explanation, internal_reference, policy_version,
                                receipt_reference, decided_at
                            ) VALUES (
                                %s, %s, %s, %s, 'APPROVED', NULL, NULL,
                                %s, %s, %s, %s
                            )
                            """,
                            (
                                decision_id,
                                request_id,
                                principal_id,
                                operator_id,
                                "internal:qualification:p006-ui-10-2-c",
                                "qualification-policy-v1",
                                receipt,
                                decided_at,
                            ),
                        )
                        cursor.execute(
                            """
                            UPDATE nexilabs_auth.developer_access_request
                            SET request_state = 'APPROVED',
                                decided_at = %s,
                                decision_reference = %s,
                                terminal_decision_id = %s
                            WHERE request_id = %s
                            """,
                            (decided_at, receipt, decision_id, request_id),
                        )
                        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")

                    authority = PostgreSQLAdminReviewAuthority(
                        _BorrowedConnectionPool(connection)
                    )
                    operator = authority.active_admin_operator(principal_id)
                    by_id = authority.active_admin_operator_by_developer_id(
                        f"  {admin_developer_id.lower()}  "
                    )
                    admin_password = authority.active_admin_password_verifier(principal_id)
                    decision = authority.developer_access_decision(request_id)
                    if operator is None or by_id is None:
                        raise AdminReviewQualificationError("C Admin Operator adapter proof failed")
                    if operator.admin_operator_id != operator_id or by_id.admin_operator_id != operator_id:
                        raise AdminReviewQualificationError("C Admin Operator identity read-back mismatch")
                    if admin_password is None or admin_password.credential_kind != ADMIN_PASSWORD_KIND:
                        raise AdminReviewQualificationError("C ADMIN_PASSWORD adapter proof failed")
                    if decision is None or decision.decision != "APPROVED":
                        raise AdminReviewQualificationError("C Developer decision adapter proof failed")
                    if decision.reviewer_principal_id != principal_id:
                        raise AdminReviewQualificationError("C reviewer attribution adapter proof failed")
                    raise _ProofRollback()
            except _ProofRollback:
                pass

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM nexilabs_auth.principal_account WHERE principal_id = %s",
                    (principal_id,),
                )
                principal_count = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT COUNT(*) FROM nexilabs_auth.admin_operator WHERE admin_operator_id = %s",
                    (operator_id,),
                )
                operator_count = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT COUNT(*) FROM nexilabs_auth.developer_access_decision WHERE decision_id = %s",
                    (decision_id,),
                )
                decision_count = int(cursor.fetchone()[0])
        if (principal_count, operator_count, decision_count) != (0, 0, 0):
            raise AdminReviewQualificationError("C adapter proof did not fully roll back synthetic authority")
        return AdminReviewAdapterQualificationReceipt(
            admin_operator_id=operator_id,
            principal_id=principal_id,
            admin_password_kind=ADMIN_PASSWORD_KIND,
            decision="APPROVED",
            request_id=request_id,
            rollback_verified=True,
        )


__all__ = [
    "B_CATALOGUES",
    "C_CATALOGUE_VERSION",
    "C_FORWARD_FILE",
    "C_MIGRATION_ID",
    "C_MILESTONE_ID",
    "C_ROLLBACK_FILE",
    "C_SEQUENCE",
    "POST_C_AUTH_TABLES",
    "PRE_C_AUTH_TABLES",
    "PostgreSQLAdminReviewQualification",
]
