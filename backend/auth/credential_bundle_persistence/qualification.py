"""P006.UI.10.2.E — PostgreSQL bundle/storage/delivery authority qualification."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from backend.auth.admin_review_persistence.qualification import (
    B_CATALOGUES,
    REQUIRED_C_COLUMNS,
    REQUIRED_C_CONSTRAINTS,
    REQUIRED_C_FUNCTIONS,
    REQUIRED_C_INDEXES,
    REQUIRED_C_TRIGGERS,
)
from backend.auth.email_verification_persistence.qualification import (
    D_MIGRATION_ID,
    D_SEQUENCE,
    POST_D_AUTH_TABLES,
    REQUIRED_D_COLUMNS,
    REQUIRED_D_CONSTRAINTS,
    REQUIRED_D_FUNCTIONS,
    REQUIRED_D_INDEXES,
    REQUIRED_D_TRIGGERS,
)

from .contracts import (
    CredentialBundleAdapterQualificationReceipt,
    CredentialBundleQualificationError,
    CredentialBundleQualificationReport,
)
from .postgresql import PostgreSQLCredentialBundleAuthority


E_MIGRATION_ID = "m006_10_02_credential_bundle_storage_delivery"
E_MILESTONE_ID = "M006.10.2"
E_SEQUENCE = 34
E_CATALOGUE_VERSION = 18
E_FORWARD_FILE = f"{E_MIGRATION_ID}.sql"
E_ROLLBACK_FILE = f"{E_MIGRATION_ID}_rollback.sql"
E_DEPENDENCY = D_MIGRATION_ID
POST_E_AUTH_TABLES = tuple(sorted((*POST_D_AUTH_TABLES,
                                   "credential_bundle",
                                   "credential_bundle_secret",
                                   "credential_delivery")))

REQUIRED_E_COLUMNS = (
    ("credential_bundle", frozenset({
        "bundle_id", "principal_id", "enigma_profile_id", "bundle_state",
        "object_provider_code", "object_key", "content_sha256", "byte_size",
        "created_at", "integrity_verified_at", "object_confirmed_at", "ready_at",
        "expires_at", "retention_until", "invalidated_at", "retired_at",
    })),
    ("credential_bundle_secret", frozenset({
        "bundle_secret_id", "bundle_id", "escrow_provider_code",
        "encrypted_secret_reference", "encryption_context_version",
        "created_at", "retired_at",
    })),
    ("credential_delivery", frozenset({
        "delivery_id", "bundle_id", "token_verifier_scheme",
        "token_verifier_version", "token_verifier_payload", "delivery_state",
        "policy_version", "logical_delivery_host_code", "issued_at", "expires_at",
        "consumed_at", "revoked_at", "download_count", "first_downloaded_at",
        "last_downloaded_at",
    })),
)
REQUIRED_E_INDEXES = frozenset({
    "ux_nexilabs_auth_current_credential_bundle",
    "ux_nexilabs_auth_credential_bundle_object",
    "ix_nexilabs_auth_credential_bundle_principal",
    "ix_nexilabs_auth_credential_bundle_state_expiry",
    "ux_nexilabs_auth_active_credential_bundle_secret",
    "ix_nexilabs_auth_credential_bundle_secret_bundle",
    "ux_nexilabs_auth_issued_credential_delivery",
    "ix_nexilabs_auth_credential_delivery_bundle",
    "ix_nexilabs_auth_credential_delivery_state_expiry",
})
REQUIRED_E_CONSTRAINTS = frozenset({
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
})
REQUIRED_E_FUNCTIONS = frozenset({
    "validate_credential_bundle_owner",
    "validate_credential_bundle_transition",
    "validate_credential_bundle_secret_transition",
    "validate_credential_delivery_transition",
    "validate_credential_delivery_bundle",
})
REQUIRED_E_TRIGGERS = frozenset({
    "tr_nexilabs_auth_credential_bundle_owner",
    "tr_nexilabs_auth_credential_bundle_transition",
    "tr_nexilabs_auth_credential_bundle_secret_transition",
    "tr_nexilabs_auth_credential_delivery_transition",
    "tr_nexilabs_auth_credential_delivery_bundle",
})


class _ProofRollback(RuntimeError):
    pass


class _BorrowedConnectionPool:
    def __init__(self, connection: Any):
        self.connection_object = connection

    @contextmanager
    def connection(self, read_only: bool = False):
        yield self.connection_object


class PostgreSQLCredentialBundleQualification:
    """Qualify E independently while treating D as immutable predecessor truth."""

    def __init__(self, pool: Any) -> None:
        if pool is None or not callable(getattr(pool, "connection", None)):
            raise TypeError("pool with connection(read_only=...) is required")
        self.pool = pool

    @staticmethod
    def _read_manifest(manifest_path: Path) -> tuple[dict[str, object], ...]:
        try:
            payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CredentialBundleQualificationError("cannot read the live migration manifest") from exc
        version = payload.get("catalogue_version")
        if isinstance(version, bool) or not isinstance(version, int) or version < E_CATALOGUE_VERSION:
            raise CredentialBundleQualificationError(
                f"E requires migration catalogue_version >= {E_CATALOGUE_VERSION}"
            )
        rows = payload.get("migrations")
        if not isinstance(rows, list) or len(rows) < E_SEQUENCE:
            raise CredentialBundleQualificationError("E requires at least 34 manifest migrations")
        result = tuple(row for row in rows if isinstance(row, dict))
        if len(result) != len(rows):
            raise CredentialBundleQualificationError("migration manifest contains a malformed row")
        prefix = tuple(int(row.get("sequence_number", -1)) for row in result[:E_SEQUENCE])
        if prefix != tuple(range(1, E_SEQUENCE + 1)):
            raise CredentialBundleQualificationError("E historical manifest prefix was renumbered")
        d_row = result[D_SEQUENCE - 1]
        if d_row.get("migration_id") != D_MIGRATION_ID or int(d_row.get("sequence_number", -1)) != D_SEQUENCE:
            raise CredentialBundleQualificationError("E requires the immutable D migration at sequence 33")
        row = result[E_SEQUENCE - 1]
        expected = {
            "migration_id": E_MIGRATION_ID,
            "milestone_id": E_MILESTONE_ID,
            "sequence_number": E_SEQUENCE,
            "forward_file": E_FORWARD_FILE,
            "rollback_file": E_ROLLBACK_FILE,
            "depends_on": [E_DEPENDENCY],
            "transaction_policy": "embedded",
            "destructive": False,
        }
        for key, value in expected.items():
            if row.get(key) != value:
                raise CredentialBundleQualificationError(f"E manifest row mismatch: {key}")
        return result

    @classmethod
    def verify_repository_artifacts(cls, repository_root: Path) -> tuple[dict[str, object], ...]:
        root = Path(repository_root)
        rows = cls._read_manifest(root / "database/migrations/migration_manifest.json")
        row = rows[E_SEQUENCE - 1]
        for filename, hash_key, size_key in (
            (E_FORWARD_FILE, "forward_sha256", "forward_byte_size"),
            (E_ROLLBACK_FILE, "rollback_sha256", "rollback_byte_size"),
        ):
            path = root / "database/migrations" / filename
            if not path.is_file():
                raise CredentialBundleQualificationError(f"missing E migration artifact: {filename}")
            raw = path.read_bytes()
            if row.get(hash_key) != sha256(raw).hexdigest():
                raise CredentialBundleQualificationError(f"E migration checksum mismatch: {filename}")
            if int(row.get(size_key, -1)) != len(raw):
                raise CredentialBundleQualificationError(f"E migration byte-size mismatch: {filename}")
        return rows

    @staticmethod
    def _assert_ledger(
        manifest_rows: tuple[dict[str, object], ...],
        ledger_rows: list[tuple[Any, ...]],
        *, minimum_count: int,
        exact_count: int | None = None,
    ) -> None:
        if exact_count is not None and len(ledger_rows) != exact_count:
            raise CredentialBundleQualificationError(
                f"database migration ledger count is {len(ledger_rows)}, expected {exact_count}"
            )
        if len(ledger_rows) < minimum_count:
            raise CredentialBundleQualificationError(
                f"database migration ledger count is {len(ledger_rows)}, expected at least {minimum_count}"
            )
        if len(ledger_rows) > len(manifest_rows):
            raise CredentialBundleQualificationError(
                "database migration ledger contains migrations unknown to the repository"
            )
        for manifest, ledger in zip(manifest_rows[:len(ledger_rows)], ledger_rows):
            migration_id, sequence_number, checksum_sha256, status = ledger
            if str(migration_id) != str(manifest.get("migration_id")):
                raise CredentialBundleQualificationError("migration ledger contains an unknown/missing migration")
            if int(sequence_number) != int(manifest.get("sequence_number", -1)):
                raise CredentialBundleQualificationError("migration ledger sequence mismatch")
            if str(checksum_sha256) != str(manifest.get("forward_sha256")):
                raise CredentialBundleQualificationError(f"migration checksum mismatch: {migration_id}")
            if str(status) != "APPLIED":
                raise CredentialBundleQualificationError(f"migration is not APPLIED: {migration_id} ({status})")

    @staticmethod
    def _auth_tables(cursor: Any) -> tuple[str, ...]:
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'nexilabs_auth' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        return tuple(str(row[0]) for row in cursor.fetchall())

    @staticmethod
    def _public_privileges(cursor: Any) -> tuple[int, int, int]:
        cursor.execute("""
            SELECT COUNT(*) FROM pg_namespace AS n
            CROSS JOIN LATERAL aclexplode(COALESCE(n.nspacl, acldefault('n', n.nspowner))) AS acl
            WHERE n.nspname = 'nexilabs_auth' AND acl.grantee = 0
        """)
        schema_count = int(cursor.fetchone()[0])
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.table_privileges
            WHERE table_schema = 'nexilabs_auth' AND grantee = 'PUBLIC'
        """)
        table_count = int(cursor.fetchone()[0])
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.routine_privileges
            WHERE routine_schema = 'nexilabs_auth' AND grantee = 'PUBLIC'
        """)
        routine_count = int(cursor.fetchone()[0])
        if schema_count or table_count or routine_count:
            raise CredentialBundleQualificationError("PUBLIC privileges are present on nexilabs_auth authority")
        return schema_count, table_count, routine_count

    @staticmethod
    def _assert_b_catalogues(cursor: Any) -> tuple[int, int]:
        cursor.execute("""
            SELECT catalogue_id, word_length, catalogue_version, catalogue_state,
                   source_reference, source_sha256
            FROM nexilabs_auth.enigma_catalogue ORDER BY word_length
        """)
        actual = tuple((str(a), int(b), int(c), str(d), str(e), str(f))
                       for a, b, c, d, e, f in cursor.fetchall())
        if actual != B_CATALOGUES:
            raise CredentialBundleQualificationError("governed B Enigma catalogue metadata differs")
        cursor.execute("""
            SELECT word_length, COUNT(*) FROM nexilabs_auth.enigma_catalogue_entry
            GROUP BY word_length ORDER BY word_length
        """)
        family_counts = tuple((int(a), int(b)) for a, b in cursor.fetchall())
        if family_counts != ((3, 93), (4, 93), (5, 93)):
            raise CredentialBundleQualificationError("governed B Enigma entry counts differ")
        return len(actual), sum(count for _, count in family_counts)

    @staticmethod
    def _count(cursor: Any, table: str) -> int:
        cursor.execute(f"SELECT COUNT(*) FROM nexilabs_auth.{table}")
        return int(cursor.fetchone()[0])

    @staticmethod
    def _assert_required_structure(
        cursor: Any, *, columns_by_table: dict[str, frozenset[str]],
        indexes: frozenset[str], constraints: frozenset[str],
        functions: frozenset[str], triggers: frozenset[str], label: str,
    ) -> None:
        for table, required in columns_by_table.items():
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'nexilabs_auth' AND table_name = %s
            """, (table,))
            present = {str(row[0]) for row in cursor.fetchall()}
            missing = sorted(required - present)
            if missing:
                raise CredentialBundleQualificationError(
                    f"missing {label} columns on {table}: {', '.join(missing)}"
                )
        cursor.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'nexilabs_auth'")
        present_indexes = {str(row[0]) for row in cursor.fetchall()}
        missing_indexes = sorted(indexes - present_indexes)
        if missing_indexes:
            raise CredentialBundleQualificationError(f"missing {label} indexes: {', '.join(missing_indexes)}")
        cursor.execute("""
            SELECT constraint_name FROM information_schema.table_constraints
            WHERE table_schema = 'nexilabs_auth'
        """)
        present_constraints = {str(row[0]) for row in cursor.fetchall()}
        missing_constraints = sorted(constraints - present_constraints)
        if missing_constraints:
            raise CredentialBundleQualificationError(
                f"missing {label} constraints: {', '.join(missing_constraints)}"
            )
        cursor.execute("""
            SELECT routine_name FROM information_schema.routines
            WHERE routine_schema = 'nexilabs_auth'
        """)
        present_functions = {str(row[0]) for row in cursor.fetchall()}
        missing_functions = sorted(functions - present_functions)
        if missing_functions:
            raise CredentialBundleQualificationError(f"missing {label} functions: {', '.join(missing_functions)}")
        cursor.execute("""
            SELECT trigger_name FROM information_schema.triggers
            WHERE trigger_schema = 'nexilabs_auth'
        """)
        present_triggers = {str(row[0]) for row in cursor.fetchall()}
        missing_triggers = sorted(triggers - present_triggers)
        if missing_triggers:
            raise CredentialBundleQualificationError(f"missing {label} triggers: {', '.join(missing_triggers)}")

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

    @classmethod
    def _assert_e_structure(cls, cursor: Any) -> None:
        cls._assert_required_structure(
            cursor,
            columns_by_table=dict(REQUIRED_E_COLUMNS),
            indexes=REQUIRED_E_INDEXES,
            constraints=REQUIRED_E_CONSTRAINTS,
            functions=REQUIRED_E_FUNCTIONS,
            triggers=REQUIRED_E_TRIGGERS,
            label="E",
        )

    def _inspect_database(
        self, *, manifest_rows: tuple[dict[str, object], ...],
        expected_database: str, phase: str,
    ) -> CredentialBundleQualificationReport:
        pre_e = phase == "pre-E"
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database()")
                database_name = str(cursor.fetchone()[0])
                if database_name != expected_database:
                    raise CredentialBundleQualificationError(
                        f"wrong database target: expected {expected_database}, got {database_name}"
                    )
                cursor.execute("SELECT COALESCE((SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()), FALSE)")
                tls_active = bool(cursor.fetchone()[0])
                if not tls_active:
                    raise CredentialBundleQualificationError("PostgreSQL TLS is not active")
                cursor.execute("""
                    SELECT migration_id, sequence_number, checksum_sha256, status
                    FROM platform.schema_migration ORDER BY sequence_number
                """)
                ledger_rows = list(cursor.fetchall())
                if pre_e:
                    self._assert_ledger(manifest_rows, ledger_rows, minimum_count=D_SEQUENCE, exact_count=D_SEQUENCE)
                else:
                    self._assert_ledger(manifest_rows, ledger_rows, minimum_count=E_SEQUENCE)

                auth_tables = self._auth_tables(cursor)
                expected_tables = POST_D_AUTH_TABLES if pre_e else POST_E_AUTH_TABLES
                if pre_e:
                    if set(auth_tables) != set(expected_tables):
                        raise CredentialBundleQualificationError(
                            "E preflight requires the exact governed post-D auth table set"
                        )
                elif set(expected_tables) - set(auth_tables):
                    raise CredentialBundleQualificationError(
                        "nexilabs_auth is missing E bundle/storage/delivery tables"
                    )

                self._assert_c_structure(cursor)
                self._assert_d_structure(cursor)
                if not pre_e:
                    self._assert_e_structure(cursor)
                schema_acl, table_acl, routine_acl = self._public_privileges(cursor)
                catalogue_count, entry_count = self._assert_b_catalogues(cursor)

                counts = {
                    "principal": self._count(cursor, "principal_account"),
                    "credential": self._count(cursor, "credential_verifier"),
                    "developer_request": self._count(cursor, "developer_access_request"),
                    "admin_operator": self._count(cursor, "admin_operator"),
                    "developer_decision": self._count(cursor, "developer_access_decision"),
                    "email_challenge": self._count(cursor, "email_verification_challenge"),
                    "enigma_profile": self._count(cursor, "enigma_profile"),
                    "principal_enigma_profile": self._count(cursor, "principal_enigma_profile"),
                    "bundle": 0 if pre_e else self._count(cursor, "credential_bundle"),
                    "bundle_secret": 0 if pre_e else self._count(cursor, "credential_bundle_secret"),
                    "delivery": 0 if pre_e else self._count(cursor, "credential_delivery"),
                }
                is_e_tail = (not pre_e and len(ledger_rows) == E_SEQUENCE)
                if pre_e or is_e_tail:
                    nonzero = {name: value for name, value in counts.items() if value != 0}
                    if nonzero:
                        raise CredentialBundleQualificationError(
                            "E persistence closure requires zero operational authority rows: "
                            + ", ".join(f"{k}={v}" for k, v in sorted(nonzero.items()))
                        )

                tail_sequence = int(ledger_rows[-1][1]) if ledger_rows else 0
                tail_id = str(ledger_rows[-1][0]) if ledger_rows else ""
                return CredentialBundleQualificationReport(
                    phase=phase,
                    database_name=database_name,
                    tls_active=tls_active,
                    repository_migration_count=len(manifest_rows),
                    database_migration_count=len(ledger_rows),
                    migration_tail_sequence=tail_sequence,
                    migration_tail_id=tail_id,
                    nexilabs_auth_tables=auth_tables,
                    public_schema_privilege_count=schema_acl,
                    public_table_privilege_count=table_acl,
                    public_routine_privilege_count=routine_acl,
                    principal_count=counts["principal"],
                    credential_count=counts["credential"],
                    developer_request_count=counts["developer_request"],
                    admin_operator_count=counts["admin_operator"],
                    developer_decision_count=counts["developer_decision"],
                    email_challenge_count=counts["email_challenge"],
                    enigma_catalogue_count=catalogue_count,
                    enigma_catalogue_entry_count=entry_count,
                    enigma_profile_count=counts["enigma_profile"],
                    principal_enigma_profile_count=counts["principal_enigma_profile"],
                    bundle_count=counts["bundle"],
                    bundle_secret_count=counts["bundle_secret"],
                    delivery_count=counts["delivery"],
                )

    def preflight(self, *, repository_root: Path, expected_database: str = "npp_dev") -> CredentialBundleQualificationReport:
        rows = self.verify_repository_artifacts(repository_root)
        return self._inspect_database(manifest_rows=rows, expected_database=expected_database, phase="pre-E")

    def verify(self, *, repository_root: Path, expected_database: str = "npp_dev") -> CredentialBundleQualificationReport:
        rows = self.verify_repository_artifacts(repository_root)
        return self._inspect_database(manifest_rows=rows, expected_database=expected_database, phase="post-E")

    def qualify_adapter(self) -> CredentialBundleAdapterQualificationReceipt:
        principal_id = "principal:qualification:p006-ui-10-2-e"
        profile_id = "enigma-profile:qualification:p006-ui-10-2-e"
        assignment_id = "enigma-assignment:qualification:p006-ui-10-2-e"
        bundle_id = "bundle:qualification:p006-ui-10-2-e"
        secret_id = "bundle-secret:qualification:p006-ui-10-2-e"
        delivery_id = "delivery:qualification:p006-ui-10-2-e"
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=15)
        retention = now + timedelta(days=30)

        with self.pool.connection(read_only=False) as connection:
            try:
                with connection.transaction():
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO nexilabs_auth.principal_account (
                                principal_id, username, username_key, identity_type, account_state
                            ) VALUES (%s, %s, %s, 'nexadevs_developer', 'PENDING')
                        """, (principal_id, "qualification_e_developer", "qualification_e_developer"))
                        cursor.execute("""
                            INSERT INTO nexilabs_auth.enigma_profile (
                                profile_id, profile_state, created_at, activated_at, profile_reference
                            ) VALUES (%s, 'ACTIVE', %s, %s, %s)
                        """, (profile_id, now, now, "qualification-e-profile"))
                        cursor.execute("""
                            INSERT INTO nexilabs_auth.principal_enigma_profile (
                                assignment_id, principal_id, profile_id, assignment_state, assigned_at
                            ) VALUES (%s, %s, %s, 'ACTIVE', %s)
                        """, (assignment_id, principal_id, profile_id, now))
                        cursor.execute("""
                            INSERT INTO nexilabs_auth.credential_bundle (
                                bundle_id, principal_id, enigma_profile_id, bundle_state,
                                object_provider_code, object_key, content_sha256, byte_size,
                                created_at, expires_at, retention_until
                            ) VALUES (
                                %s, %s, %s, 'GENERATED', 'QUALIFICATION_PRIVATE_OBJECT',
                                %s, %s, 4096, %s, %s, %s
                            )
                        """, (bundle_id, principal_id, profile_id,
                              "qualification/private/bundle-e.zip", "a" * 64,
                              now, expires, retention))
                        cursor.execute("""
                            UPDATE nexilabs_auth.credential_bundle
                            SET integrity_verified_at = %s,
                                object_confirmed_at = %s,
                                ready_at = %s,
                                bundle_state = 'READY'
                            WHERE bundle_id = %s
                        """, (now, now, now, bundle_id))
                        cursor.execute("""
                            INSERT INTO nexilabs_auth.credential_bundle_secret (
                                bundle_secret_id, bundle_id, escrow_provider_code,
                                encrypted_secret_reference, encryption_context_version, created_at
                            ) VALUES (%s, %s, 'QUALIFICATION_KMS_REFERENCE', %s, 'ctx-v1', %s)
                        """, (secret_id, bundle_id, "opaque-encrypted-secret-reference-qualification-e", now))
                        cursor.execute("""
                            INSERT INTO nexilabs_auth.credential_delivery (
                                delivery_id, bundle_id, token_verifier_scheme,
                                token_verifier_version, token_verifier_payload,
                                delivery_state, policy_version, logical_delivery_host_code,
                                issued_at, expires_at, download_count
                            ) VALUES (
                                %s, %s, 'qualification-keyed-v1', 1, %s,
                                'ISSUED', 'qualification-policy-v1',
                                'CREDENTIAL_DELIVERY_QUALIFICATION', %s, %s, 0
                            )
                        """, (delivery_id, bundle_id,
                              "opaque-delivery-token-verifier-qualification-e", now, expires))

                    authority = PostgreSQLCredentialBundleAuthority(_BorrowedConnectionPool(connection))
                    bundle = authority.ready_bundle_for_principal(principal_id)
                    secret = authority.active_secret_reference(bundle_id)
                    delivery = authority.issued_delivery_for_bundle(bundle_id)
                    if bundle is None or bundle.bundle_id != bundle_id or bundle.enigma_profile_id != profile_id:
                        raise CredentialBundleQualificationError("E adapter proof bundle read-back mismatch")
                    if secret is None or secret.bundle_secret_id != secret_id:
                        raise CredentialBundleQualificationError("E adapter proof secret read-back mismatch")
                    if delivery is None or delivery.delivery_id != delivery_id:
                        raise CredentialBundleQualificationError("E adapter proof delivery read-back mismatch")

                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE nexilabs_auth.credential_delivery
                            SET download_count = 1,
                                first_downloaded_at = %s,
                                last_downloaded_at = %s,
                                consumed_at = %s,
                                delivery_state = 'CONSUMED'
                            WHERE delivery_id = %s
                        """, (now, now, now, delivery_id))
                    terminal = authority.delivery_by_id(delivery_id)
                    if terminal is None or terminal.delivery_state != "CONSUMED" or terminal.download_count != 1:
                        raise CredentialBundleQualificationError("E adapter proof delivery lifecycle mismatch")
                    raise _ProofRollback()
            except _ProofRollback:
                pass

            with connection.cursor() as cursor:
                checks = []
                for table, column, value in (
                    ("principal_account", "principal_id", principal_id),
                    ("enigma_profile", "profile_id", profile_id),
                    ("principal_enigma_profile", "assignment_id", assignment_id),
                    ("credential_bundle", "bundle_id", bundle_id),
                    ("credential_bundle_secret", "bundle_secret_id", secret_id),
                    ("credential_delivery", "delivery_id", delivery_id),
                ):
                    cursor.execute(f"SELECT COUNT(*) FROM nexilabs_auth.{table} WHERE {column} = %s", (value,))
                    checks.append(int(cursor.fetchone()[0]))
        if any(checks):
            raise CredentialBundleQualificationError("E adapter proof did not fully roll back synthetic authority")
        return CredentialBundleAdapterQualificationReceipt(
            bundle_id=bundle_id,
            principal_id=principal_id,
            enigma_profile_id=profile_id,
            bundle_secret_id=secret_id,
            delivery_id=delivery_id,
            bundle_state="READY",
            delivery_state="CONSUMED",
            rollback_verified=True,
        )


__all__ = [
    "E_CATALOGUE_VERSION", "E_FORWARD_FILE", "E_MIGRATION_ID", "E_MILESTONE_ID",
    "E_ROLLBACK_FILE", "E_SEQUENCE", "POST_E_AUTH_TABLES",
    "PostgreSQLCredentialBundleQualification", "REQUIRED_E_COLUMNS",
    "REQUIRED_E_CONSTRAINTS", "REQUIRED_E_FUNCTIONS", "REQUIRED_E_INDEXES",
    "REQUIRED_E_TRIGGERS",
]
