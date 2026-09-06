"""P006.UI.10.2.D — PostgreSQL challenge, ledger, ACL and adapter qualification."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from backend.auth.admin_review_persistence.qualification import (
    B_CATALOGUES,
    C_MIGRATION_ID,
    C_SEQUENCE,
    POST_C_AUTH_TABLES,
    REQUIRED_C_COLUMNS,
    REQUIRED_C_CONSTRAINTS,
    REQUIRED_C_FUNCTIONS,
    REQUIRED_C_INDEXES,
    REQUIRED_C_TRIGGERS,
)

from .contracts import (
    EmailVerificationAdapterQualificationReceipt,
    EmailVerificationQualificationError,
    EmailVerificationQualificationReport,
)
from .postgresql import PostgreSQLEmailVerificationAuthority


D_MIGRATION_ID = "m006_10_02_email_verification_challenge"
D_MILESTONE_ID = "M006.10.2"
D_SEQUENCE = 33
D_CATALOGUE_VERSION = 17
D_FORWARD_FILE = f"{D_MIGRATION_ID}.sql"
D_ROLLBACK_FILE = f"{D_MIGRATION_ID}_rollback.sql"
D_DEPENDENCY = C_MIGRATION_ID
POST_D_AUTH_TABLES = tuple(sorted((*POST_C_AUTH_TABLES, "email_verification_challenge")))

REQUIRED_D_INDEXES = frozenset(
    {
        "ux_nexilabs_auth_issued_email_verification_challenge",
        "ix_nexilabs_auth_email_verification_challenge_principal",
        "ix_nexilabs_auth_email_verification_challenge_state_expiry",
    }
)
REQUIRED_D_CONSTRAINTS = frozenset(
    {
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
)
REQUIRED_D_FUNCTIONS = frozenset(
    {
        "validate_email_verification_challenge_email",
        "validate_email_verification_challenge_transition",
    }
)
REQUIRED_D_TRIGGERS = frozenset(
    {
        "tr_nexilabs_auth_email_verification_challenge_email",
        "tr_nexilabs_auth_email_verification_challenge_transition",
    }
)
REQUIRED_D_COLUMNS = frozenset(
    {
        "challenge_id",
        "principal_id",
        "email_id",
        "otp_verifier_scheme",
        "otp_verifier_version",
        "otp_verifier_payload",
        "challenge_state",
        "policy_version",
        "issued_at",
        "expires_at",
        "consumed_at",
        "invalidated_at",
        "attempt_count",
        "max_attempts",
        "resend_count",
        "last_resend_at",
    }
)


class _ProofRollback(RuntimeError):
    pass


class _BorrowedConnectionPool:
    def __init__(self, connection: Any):
        self.connection_object = connection

    @contextmanager
    def connection(self, read_only: bool = False):
        yield self.connection_object


class PostgreSQLEmailVerificationQualification:
    """Qualify D without changing or invoking C's closed qualification contract."""

    def __init__(self, pool: Any) -> None:
        if pool is None or not callable(getattr(pool, "connection", None)):
            raise TypeError("pool with connection(read_only=...) is required")
        self.pool = pool

    @staticmethod
    def _read_manifest(manifest_path: Path) -> tuple[dict[str, object], ...]:
        try:
            payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise EmailVerificationQualificationError(
                "cannot read the live migration manifest"
            ) from exc

        catalogue_version = payload.get("catalogue_version")
        if (
            isinstance(catalogue_version, bool)
            or not isinstance(catalogue_version, int)
            or catalogue_version < D_CATALOGUE_VERSION
        ):
            raise EmailVerificationQualificationError(
                f"D requires migration catalogue_version >= {D_CATALOGUE_VERSION}"
            )
        rows = payload.get("migrations")
        if not isinstance(rows, list) or len(rows) < D_SEQUENCE:
            raise EmailVerificationQualificationError(
                "D requires at least 33 manifest migrations"
            )
        result = tuple(row for row in rows if isinstance(row, dict))
        if len(result) != len(rows):
            raise EmailVerificationQualificationError(
                "migration manifest contains a malformed row"
            )
        prefix_sequences = tuple(
            int(row.get("sequence_number", -1)) for row in result[:D_SEQUENCE]
        )
        if prefix_sequences != tuple(range(1, D_SEQUENCE + 1)):
            raise EmailVerificationQualificationError(
                "D historical manifest prefix was renumbered"
            )
        c_row = result[C_SEQUENCE - 1]
        if (
            c_row.get("migration_id") != C_MIGRATION_ID
            or int(c_row.get("sequence_number", -1)) != C_SEQUENCE
        ):
            raise EmailVerificationQualificationError(
                "D requires the immutable C migration at sequence 32"
            )
        row = result[D_SEQUENCE - 1]
        expected = {
            "migration_id": D_MIGRATION_ID,
            "milestone_id": D_MILESTONE_ID,
            "sequence_number": D_SEQUENCE,
            "forward_file": D_FORWARD_FILE,
            "rollback_file": D_ROLLBACK_FILE,
            "depends_on": [D_DEPENDENCY],
            "transaction_policy": "embedded",
            "destructive": False,
        }
        for key, value in expected.items():
            if row.get(key) != value:
                raise EmailVerificationQualificationError(
                    f"D manifest row mismatch: {key}"
                )
        return result

    @classmethod
    def verify_repository_artifacts(
        cls, repository_root: Path
    ) -> tuple[dict[str, object], ...]:
        root = Path(repository_root)
        rows = cls._read_manifest(
            root / "database" / "migrations" / "migration_manifest.json"
        )
        row = rows[D_SEQUENCE - 1]
        for filename, hash_key, size_key in (
            (D_FORWARD_FILE, "forward_sha256", "forward_byte_size"),
            (D_ROLLBACK_FILE, "rollback_sha256", "rollback_byte_size"),
        ):
            path = root / "database" / "migrations" / filename
            if not path.is_file():
                raise EmailVerificationQualificationError(
                    f"missing D migration artifact: {filename}"
                )
            raw = path.read_bytes()
            if row.get(hash_key) != sha256(raw).hexdigest():
                raise EmailVerificationQualificationError(
                    f"D migration checksum mismatch: {filename}"
                )
            if int(row.get(size_key, -1)) != len(raw):
                raise EmailVerificationQualificationError(
                    f"D migration byte-size mismatch: {filename}"
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
            raise EmailVerificationQualificationError(
                f"database migration ledger count is {len(ledger_rows)}, expected {exact_count}"
            )
        if len(ledger_rows) < minimum_count:
            raise EmailVerificationQualificationError(
                f"database migration ledger count is {len(ledger_rows)}, expected at least {minimum_count}"
            )
        if len(ledger_rows) > len(manifest_rows):
            raise EmailVerificationQualificationError(
                "database migration ledger contains migrations unknown to the repository"
            )
        for manifest, ledger in zip(manifest_rows[: len(ledger_rows)], ledger_rows):
            migration_id, sequence_number, checksum_sha256, status = ledger
            if str(migration_id) != str(manifest.get("migration_id")):
                raise EmailVerificationQualificationError(
                    "migration ledger contains an unknown/missing migration"
                )
            if int(sequence_number) != int(manifest.get("sequence_number", -1)):
                raise EmailVerificationQualificationError(
                    "migration ledger sequence mismatch"
                )
            if str(checksum_sha256) != str(manifest.get("forward_sha256")):
                raise EmailVerificationQualificationError(
                    f"migration checksum mismatch: {migration_id}"
                )
            if str(status) != "APPLIED":
                raise EmailVerificationQualificationError(
                    f"migration is not APPLIED: {migration_id} ({status})"
                )

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
            raise EmailVerificationQualificationError(
                "PUBLIC privileges are present on nexilabs_auth authority"
            )
        return schema_count, table_count, routine_count

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
            raise EmailVerificationQualificationError(
                "governed B Enigma catalogue metadata differs"
            )
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
            raise EmailVerificationQualificationError(
                "governed B Enigma entry counts differ"
            )
        return len(actual), sum(count for _, count in family_counts)

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
    def _count(cursor: Any, table: str) -> int:
        cursor.execute(f"SELECT COUNT(*) FROM nexilabs_auth.{table}")
        return int(cursor.fetchone()[0])

    @classmethod
    def _authority_counts(cls, cursor: Any) -> dict[str, int]:
        return {
            "principal": cls._count(cursor, "principal_account"),
            "credential": cls._count(cursor, "credential_verifier"),
            "developer_request": cls._count(cursor, "developer_access_request"),
            "admin_operator": cls._count(cursor, "admin_operator"),
            "developer_decision": cls._count(cursor, "developer_access_decision"),
            "enigma_profile": cls._count(cursor, "enigma_profile"),
            "principal_enigma_profile": cls._count(cursor, "principal_enigma_profile"),
        }

    @staticmethod
    def _assert_required_structure(
        cursor: Any,
        *,
        columns_by_table: dict[str, frozenset[str]],
        indexes: frozenset[str],
        constraints: frozenset[str],
        functions: frozenset[str],
        triggers: frozenset[str],
        label: str,
    ) -> None:
        for table, required in columns_by_table.items():
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
                raise EmailVerificationQualificationError(
                    f"missing {label} columns on {table}: {', '.join(missing)}"
                )

        cursor.execute(
            "SELECT indexname FROM pg_indexes WHERE schemaname = 'nexilabs_auth'"
        )
        present_indexes = {str(row[0]) for row in cursor.fetchall()}
        missing_indexes = sorted(indexes - present_indexes)
        if missing_indexes:
            raise EmailVerificationQualificationError(
                f"missing {label} indexes: {', '.join(missing_indexes)}"
            )

        cursor.execute(
            """
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_schema = 'nexilabs_auth'
            """
        )
        present_constraints = {str(row[0]) for row in cursor.fetchall()}
        missing_constraints = sorted(constraints - present_constraints)
        if missing_constraints:
            raise EmailVerificationQualificationError(
                f"missing {label} constraints: {', '.join(missing_constraints)}"
            )

        cursor.execute(
            """
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_schema = 'nexilabs_auth'
            """
        )
        present_functions = {str(row[0]) for row in cursor.fetchall()}
        missing_functions = sorted(functions - present_functions)
        if missing_functions:
            raise EmailVerificationQualificationError(
                f"missing {label} functions: {', '.join(missing_functions)}"
            )

        cursor.execute(
            """
            SELECT trigger_name
            FROM information_schema.triggers
            WHERE trigger_schema = 'nexilabs_auth'
            """
        )
        present_triggers = {str(row[0]) for row in cursor.fetchall()}
        missing_triggers = sorted(triggers - present_triggers)
        if missing_triggers:
            raise EmailVerificationQualificationError(
                f"missing {label} triggers: {', '.join(missing_triggers)}"
            )

    @classmethod
    def _assert_c_structure(cls, cursor: Any) -> None:
        cls._assert_required_structure(
            cursor,
            columns_by_table=dict(REQUIRED_C_COLUMNS),
            indexes=REQUIRED_C_INDEXES,
            constraints=REQUIRED_C_CONSTRAINTS,
            functions=REQUIRED_C_FUNCTIONS,
            triggers=REQUIRED_C_TRIGGERS,
            label="C",
        )

    @classmethod
    def _assert_d_structure(cls, cursor: Any) -> None:
        cls._assert_required_structure(
            cursor,
            columns_by_table={"email_verification_challenge": REQUIRED_D_COLUMNS},
            indexes=REQUIRED_D_INDEXES,
            constraints=REQUIRED_D_CONSTRAINTS,
            functions=REQUIRED_D_FUNCTIONS,
            triggers=REQUIRED_D_TRIGGERS,
            label="D",
        )

    def _inspect_database(
        self,
        *,
        manifest_rows: tuple[dict[str, object], ...],
        expected_database: str,
        phase: str,
    ) -> EmailVerificationQualificationReport:
        pre_d = phase == "pre-D"
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database()")
                database_name = str(cursor.fetchone()[0])
                if database_name != expected_database:
                    raise EmailVerificationQualificationError(
                        f"wrong database target: expected {expected_database}, got {database_name}"
                    )
                cursor.execute(
                    "SELECT COALESCE((SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()), FALSE)"
                )
                tls_active = bool(cursor.fetchone()[0])
                if not tls_active:
                    raise EmailVerificationQualificationError(
                        "PostgreSQL TLS is not active"
                    )
                cursor.execute(
                    """
                    SELECT migration_id, sequence_number, checksum_sha256, status
                    FROM platform.schema_migration
                    ORDER BY sequence_number
                    """
                )
                ledger_rows = list(cursor.fetchall())
                if pre_d:
                    self._assert_ledger(
                        manifest_rows,
                        ledger_rows,
                        minimum_count=C_SEQUENCE,
                        exact_count=C_SEQUENCE,
                    )
                else:
                    self._assert_ledger(
                        manifest_rows,
                        ledger_rows,
                        minimum_count=D_SEQUENCE,
                    )

                auth_tables = self._auth_tables(cursor)
                expected_tables = POST_C_AUTH_TABLES if pre_d else POST_D_AUTH_TABLES
                if pre_d:
                    if set(auth_tables) != set(expected_tables):
                        raise EmailVerificationQualificationError(
                            "D preflight requires the exact governed post-C auth table set"
                        )
                elif set(expected_tables) - set(auth_tables):
                    raise EmailVerificationQualificationError(
                        "nexilabs_auth is missing the D challenge table"
                    )

                self._assert_c_structure(cursor)
                if not pre_d:
                    self._assert_d_structure(cursor)
                schema_acl, table_acl, routine_acl = self._public_privileges(cursor)
                catalogue_count, entry_count = self._assert_b_catalogues(cursor)
                counts = self._authority_counts(cursor)
                challenge_count = (
                    0
                    if pre_d
                    else self._count(cursor, "email_verification_challenge")
                )

        if pre_d:
            if (
                int(ledger_rows[-1][1]) != C_SEQUENCE
                or str(ledger_rows[-1][0]) != C_MIGRATION_ID
            ):
                raise EmailVerificationQualificationError(
                    "D preflight requires the database to be exactly at the C migration"
                )
            for label, value in counts.items():
                if value != 0:
                    raise EmailVerificationQualificationError(
                        f"D preflight requires zero predecessor {label} rows, found {value}"
                    )
        else:
            if int(ledger_rows[D_SEQUENCE - 1][1]) != D_SEQUENCE or str(
                ledger_rows[D_SEQUENCE - 1][0]
            ) != D_MIGRATION_ID:
                raise EmailVerificationQualificationError(
                    "D migration is not present at sequence 33"
                )
            if len(ledger_rows) == D_SEQUENCE:
                for label, value in counts.items():
                    if value != 0:
                        raise EmailVerificationQualificationError(
                            f"D persistence closure requires zero {label} rows, found {value}"
                        )
                if challenge_count != 0:
                    raise EmailVerificationQualificationError(
                        f"D persistence closure requires zero challenge rows, found {challenge_count}"
                    )

        return EmailVerificationQualificationReport(
            phase=phase,
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
            email_challenge_count=challenge_count,
            enigma_catalogue_count=catalogue_count,
            enigma_catalogue_entry_count=entry_count,
            enigma_profile_count=counts["enigma_profile"],
            principal_enigma_profile_count=counts["principal_enigma_profile"],
        )

    def preflight(
        self, *, repository_root: Path, expected_database: str = "npp_dev"
    ) -> EmailVerificationQualificationReport:
        rows = self.verify_repository_artifacts(repository_root)
        return self._inspect_database(
            manifest_rows=rows,
            expected_database=expected_database,
            phase="pre-D",
        )

    def verify(
        self, *, repository_root: Path, expected_database: str = "npp_dev"
    ) -> EmailVerificationQualificationReport:
        rows = self.verify_repository_artifacts(repository_root)
        return self._inspect_database(
            manifest_rows=rows,
            expected_database=expected_database,
            phase="post-D",
        )

    def qualify_adapter(self) -> EmailVerificationAdapterQualificationReceipt:
        principal_id = "principal:qualification:p006-ui-10-2-d"
        email_id = "email:qualification:p006-ui-10-2-d"
        challenge_id = "email-challenge:qualification:p006-ui-10-2-d"
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=10)

        with self.pool.connection(read_only=False) as connection:
            try:
                with connection.transaction():
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.principal_account (
                                principal_id, username, username_key,
                                identity_type, account_state
                            ) VALUES (
                                %s, %s, %s, 'nexadevs_developer', 'PENDING'
                            )
                            """,
                            (
                                principal_id,
                                "qualification_d_developer",
                                "qualification_d_developer",
                            ),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.account_email (
                                email_id, principal_id, email_address, email_key,
                                verification_state, is_primary,
                                verification_requested_at
                            ) VALUES (%s, %s, %s, %s, 'PENDING', TRUE, %s)
                            """,
                            (
                                email_id,
                                principal_id,
                                "qualification-d@example.invalid",
                                "qualification-d@example.invalid",
                                now,
                            ),
                        )
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.email_verification_challenge (
                                challenge_id, principal_id, email_id,
                                otp_verifier_scheme, otp_verifier_version,
                                otp_verifier_payload, challenge_state,
                                policy_version, issued_at, expires_at,
                                attempt_count, max_attempts, resend_count
                            ) VALUES (
                                %s, %s, %s, 'qualification-keyed-v1', 1,
                                %s, 'ISSUED', 'qualification-policy-v1',
                                %s, %s, 0, 3, 0
                            )
                            """,
                            (
                                challenge_id,
                                principal_id,
                                email_id,
                                "opaque-qualification-verifier-payload-0001",
                                now,
                                expires,
                            ),
                        )
                        cursor.execute(
                            """
                            UPDATE nexilabs_auth.email_verification_challenge
                            SET attempt_count = max_attempts,
                                challenge_state = 'LOCKED'
                            WHERE challenge_id = %s
                            """,
                            (challenge_id,),
                        )

                    authority = PostgreSQLEmailVerificationAuthority(
                        _BorrowedConnectionPool(connection)
                    )
                    record = authority.challenge_by_id(challenge_id)
                    if record is None:
                        raise EmailVerificationQualificationError(
                            "D adapter proof could not read synthetic challenge"
                        )
                    if record.challenge_state != "LOCKED":
                        raise EmailVerificationQualificationError(
                            "D adapter proof lifecycle read-back mismatch"
                        )
                    if record.principal_id != principal_id or record.email_id != email_id:
                        raise EmailVerificationQualificationError(
                            "D adapter proof owner read-back mismatch"
                        )
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
                    "SELECT COUNT(*) FROM nexilabs_auth.account_email WHERE email_id = %s",
                    (email_id,),
                )
                email_count = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT COUNT(*) FROM nexilabs_auth.email_verification_challenge WHERE challenge_id = %s",
                    (challenge_id,),
                )
                challenge_count = int(cursor.fetchone()[0])
        if (principal_count, email_count, challenge_count) != (0, 0, 0):
            raise EmailVerificationQualificationError(
                "D adapter proof did not fully roll back synthetic authority"
            )
        return EmailVerificationAdapterQualificationReceipt(
            challenge_id=challenge_id,
            principal_id=principal_id,
            email_id=email_id,
            challenge_state="LOCKED",
            verifier_scheme="qualification-keyed-v1",
            rollback_verified=True,
        )


__all__ = [
    "D_CATALOGUE_VERSION",
    "D_FORWARD_FILE",
    "D_MIGRATION_ID",
    "D_MILESTONE_ID",
    "D_ROLLBACK_FILE",
    "D_SEQUENCE",
    "POST_D_AUTH_TABLES",
    "PostgreSQLEmailVerificationQualification",
    "REQUIRED_D_COLUMNS",
    "REQUIRED_D_CONSTRAINTS",
    "REQUIRED_D_FUNCTIONS",
    "REQUIRED_D_INDEXES",
    "REQUIRED_D_TRIGGERS",
]
