"""P006.UI.10.2.B — Governed PostgreSQL Enigma catalogue admission boundary."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable

from .contracts import (
    EXPECTED_TOTAL_ROW_COUNT,
    WORD_LENGTHS,
    EnigmaAdapterQualificationReceipt,
    EnigmaAdmissionReceipt,
    EnigmaDatabaseQualificationError,
    EnigmaReadBackReceipt,
    PostgreSQLPreflightReport,
    QualifiedEnigmaSource,
)


EXPECTED_AUTH_TABLES = (
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

_ALLOWED_TRANSITIONS = {
    "DRAFT": frozenset({"QUALIFIED"}),
    "QUALIFIED": frozenset({"ACTIVE"}),
    "ACTIVE": frozenset({"RETIRED"}),
    "RETIRED": frozenset(),
}


def validate_catalogue_transition(current_state: str, target_state: str) -> None:
    current = str(current_state)
    target = str(target_state)
    if target not in _ALLOWED_TRANSITIONS.get(current, frozenset()):
        raise EnigmaDatabaseQualificationError(
            f"invalid Enigma catalogue lifecycle transition: {current} -> {target}"
        )


class _QualificationRollback(RuntimeError):
    pass


class _BorrowedConnectionPool:
    """Give the read adapter the current qualification transaction connection."""

    def __init__(self, connection: Any):
        self.connection_object = connection

    @contextmanager
    def connection(self, read_only: bool = False):
        yield self.connection_object


class PostgreSQLEnigmaCatalogueAdmission:
    """Admission and read-back operations over migration-31 Enigma authority.

    The class assumes schema creation is historical truth. It creates no tables
    and performs no migration. Source qualification must happen before calling
    ``admit``.
    """

    def __init__(self, pool: Any):
        if pool is None or not callable(getattr(pool, "connection", None)):
            raise TypeError("pool with connection(read_only=...) is required")
        self.pool = pool

    @staticmethod
    def _manifest_rows(manifest_path: Path) -> tuple[dict[str, object], ...]:
        payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        migrations = payload.get("migrations")
        if not isinstance(migrations, list) or not migrations:
            raise EnigmaDatabaseQualificationError("migration manifest is malformed or empty")
        result: list[dict[str, object]] = []
        for row in migrations:
            if not isinstance(row, dict):
                raise EnigmaDatabaseQualificationError("migration manifest contains a malformed row")
            result.append(row)
        return tuple(result)

    def preflight(
        self,
        *,
        manifest_path: Path,
        expected_database: str = "npp_dev",
        require_empty_catalogue_authority: bool = False,
    ) -> PostgreSQLPreflightReport:
        manifest_rows = self._manifest_rows(manifest_path)
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database()")
                database_name = str(cursor.fetchone()[0])
                if database_name != expected_database:
                    raise EnigmaDatabaseQualificationError(
                        f"wrong database target: expected {expected_database}, got {database_name}"
                    )

                cursor.execute(
                    "SELECT COALESCE((SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()), FALSE)"
                )
                tls_active = bool(cursor.fetchone()[0])
                if not tls_active:
                    raise EnigmaDatabaseQualificationError("PostgreSQL TLS is not active")

                cursor.execute(
                    """
                    SELECT migration_id, sequence_number, checksum_sha256, status
                    FROM platform.schema_migration
                    ORDER BY sequence_number
                    """
                )
                ledger_rows = list(cursor.fetchall())
                if len(ledger_rows) != len(manifest_rows):
                    raise EnigmaDatabaseQualificationError(
                        "migration ledger count differs from the live repository manifest"
                    )
                for manifest, ledger in zip(manifest_rows, ledger_rows):
                    migration_id, sequence_number, checksum_sha256, status = ledger
                    if str(migration_id) != str(manifest.get("migration_id")):
                        raise EnigmaDatabaseQualificationError("migration ledger contains an unknown/missing migration")
                    if int(sequence_number) != int(manifest.get("sequence_number", -1)):
                        raise EnigmaDatabaseQualificationError("migration ledger sequence mismatch")
                    if str(checksum_sha256) != str(manifest.get("forward_sha256")):
                        raise EnigmaDatabaseQualificationError(
                            f"migration checksum mismatch: {migration_id}"
                        )
                    if str(status) != "APPLIED":
                        raise EnigmaDatabaseQualificationError(
                            f"migration is not APPLIED: {migration_id} ({status})"
                        )

                cursor.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'nexilabs_auth'
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    """
                )
                auth_tables = tuple(str(row[0]) for row in cursor.fetchall())
                if auth_tables != EXPECTED_AUTH_TABLES:
                    raise EnigmaDatabaseQualificationError(
                        "nexilabs_auth base-table set differs from migration-31 authority"
                    )

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
                public_schema_privileges = int(cursor.fetchone()[0])
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.table_privileges
                    WHERE table_schema = 'nexilabs_auth'
                      AND grantee = 'PUBLIC'
                    """
                )
                public_table_privileges = int(cursor.fetchone()[0])
                if public_schema_privileges or public_table_privileges:
                    raise EnigmaDatabaseQualificationError(
                        "PUBLIC privileges are present on nexilabs_auth authority"
                    )

                counts: dict[str, int] = {}
                for label, table in (
                    ("principal", "principal_account"),
                    ("catalogue", "enigma_catalogue"),
                    ("catalogue_entry", "enigma_catalogue_entry"),
                    ("profile", "enigma_profile"),
                    ("principal_profile_assignment", "principal_enigma_profile"),
                ):
                    cursor.execute(f"SELECT COUNT(*) FROM nexilabs_auth.{table}")
                    counts[label] = int(cursor.fetchone()[0])

        report = PostgreSQLPreflightReport(
            database_name=database_name,
            tls_active=tls_active,
            repository_migration_count=len(manifest_rows),
            database_migration_count=len(ledger_rows),
            migration_tail_sequence=int(ledger_rows[-1][1]),
            migration_tail_id=str(ledger_rows[-1][0]),
            nexilabs_auth_tables=auth_tables,
            public_schema_privilege_count=public_schema_privileges,
            public_table_privilege_count=public_table_privileges,
            principal_count=counts["principal"],
            catalogue_count=counts["catalogue"],
            catalogue_entry_count=counts["catalogue_entry"],
            profile_count=counts["profile"],
            principal_profile_assignment_count=counts["principal_profile_assignment"],
        )
        if require_empty_catalogue_authority:
            if report.catalogue_count != 0 or report.catalogue_entry_count != 0:
                raise EnigmaDatabaseQualificationError(
                    "initial .10.2.B admission requires empty Enigma catalogue authority"
                )
            if report.profile_count != 0 or report.principal_profile_assignment_count != 0:
                raise EnigmaDatabaseQualificationError(
                    "initial .10.2.B admission requires zero Enigma profiles/assignments"
                )
            if report.principal_count != 0:
                raise EnigmaDatabaseQualificationError(
                    "initial .10.2.B admission refuses an unexpected principal population"
                )
        return report

    @staticmethod
    def _expected_catalogue_metadata(
        sources: Iterable[QualifiedEnigmaSource],
    ) -> dict[str, tuple[int, int, str, str]]:
        return {
            source.spec.catalogue_id: (
                source.spec.word_length,
                source.spec.catalogue_version,
                source.spec.source_reference,
                source.sha256,
            )
            for source in sources
        }

    @staticmethod
    def _expected_entries(
        sources: Iterable[QualifiedEnigmaSource],
    ) -> dict[tuple[str, int, str], tuple[int, tuple[str, str, str]]]:
        expected: dict[tuple[str, int, str], tuple[int, tuple[str, str, str]]] = {}
        for source in sources:
            for row in source.rows:
                expected[(source.spec.catalogue_id, row.day_of_month, row.period)] = (
                    source.spec.word_length,
                    row.words,
                )
        return expected

    @classmethod
    def _assert_cursor_parity(
        cls,
        cursor: Any,
        sources: tuple[QualifiedEnigmaSource, ...],
        *,
        expected_state: str,
    ) -> None:
        catalogue_ids = tuple(source.spec.catalogue_id for source in sources)
        cursor.execute(
            """
            SELECT catalogue_id, word_length, catalogue_version, catalogue_state,
                   source_reference, source_sha256
            FROM nexilabs_auth.enigma_catalogue
            WHERE catalogue_id = ANY(%s)
            ORDER BY word_length
            """,
            (list(catalogue_ids),),
        )
        actual_catalogues = list(cursor.fetchall())
        if len(actual_catalogues) != len(sources):
            raise EnigmaDatabaseQualificationError("catalogue metadata read-back count mismatch")
        expected_metadata = cls._expected_catalogue_metadata(sources)
        for row in actual_catalogues:
            catalogue_id, word_length, version, state, source_reference, source_sha256 = row
            expected = expected_metadata.get(str(catalogue_id))
            if expected is None:
                raise EnigmaDatabaseQualificationError("unexpected catalogue returned during parity proof")
            if (
                int(word_length),
                int(version),
                str(source_reference),
                str(source_sha256),
            ) != expected:
                raise EnigmaDatabaseQualificationError(
                    f"catalogue provenance/version mismatch: {catalogue_id}"
                )
            if str(state) != expected_state:
                raise EnigmaDatabaseQualificationError(
                    f"catalogue lifecycle mismatch: {catalogue_id} is {state}"
                )

        cursor.execute(
            """
            SELECT catalogue_id, word_length, day_of_month, period,
                   word_1, word_2, word_3
            FROM nexilabs_auth.enigma_catalogue_entry
            WHERE catalogue_id = ANY(%s)
            ORDER BY word_length, day_of_month,
                     CASE period WHEN 'Morning' THEN 1 WHEN 'Noon' THEN 2 ELSE 3 END
            """,
            (list(catalogue_ids),),
        )
        actual_entries = list(cursor.fetchall())
        expected_entries = cls._expected_entries(sources)
        if len(actual_entries) != len(expected_entries):
            raise EnigmaDatabaseQualificationError("catalogue entry read-back count mismatch")
        for row in actual_entries:
            catalogue_id, word_length, day, period, word_1, word_2, word_3 = row
            key = (str(catalogue_id), int(day), str(period))
            expected = expected_entries.get(key)
            if expected is None:
                raise EnigmaDatabaseQualificationError(
                    f"unexpected catalogue authority key during read-back: {key}"
                )
            expected_word_length, expected_words = expected
            if int(word_length) != expected_word_length or tuple(map(str, (word_1, word_2, word_3))) != expected_words:
                raise EnigmaDatabaseQualificationError(
                    f"catalogue challenge material mismatch at {key}"
                )

    def admit(
        self,
        sources: tuple[QualifiedEnigmaSource, ...],
        *,
        qualified_at: datetime | None = None,
    ) -> EnigmaAdmissionReceipt:
        if tuple(source.spec.word_length for source in sources) != WORD_LENGTHS:
            raise EnigmaDatabaseQualificationError("admission requires exactly the 3/4/5 families")
        if sum(source.row_count for source in sources) != EXPECTED_TOTAL_ROW_COUNT:
            raise EnigmaDatabaseQualificationError("admission requires exactly 279 qualified shared rows")
        when = qualified_at or datetime.now(timezone.utc)
        catalogue_ids = tuple(source.spec.catalogue_id for source in sources)

        with self.pool.connection(read_only=False) as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT catalogue_id, word_length, catalogue_version, catalogue_state
                        FROM nexilabs_auth.enigma_catalogue
                        WHERE word_length IN (3, 4, 5)
                        FOR UPDATE
                        """
                    )
                    existing = list(cursor.fetchall())
                    if existing:
                        raise EnigmaDatabaseQualificationError(
                            "initial v1 admission refuses to mutate/overwrite existing Enigma catalogue history"
                        )
                    cursor.execute("SELECT COUNT(*) FROM nexilabs_auth.enigma_catalogue_entry")
                    if int(cursor.fetchone()[0]) != 0:
                        raise EnigmaDatabaseQualificationError(
                            "initial v1 admission refuses non-empty Enigma catalogue entries"
                        )

                    for source in sources:
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.enigma_catalogue (
                                catalogue_id, word_length, catalogue_version,
                                catalogue_state, source_reference, source_sha256
                            ) VALUES (%s, %s, %s, 'DRAFT', %s, %s)
                            """,
                            (
                                source.spec.catalogue_id,
                                source.spec.word_length,
                                source.spec.catalogue_version,
                                source.spec.source_reference,
                                source.sha256,
                            ),
                        )
                        for row in source.rows:
                            cursor.execute(
                                """
                                INSERT INTO nexilabs_auth.enigma_catalogue_entry (
                                    catalogue_id, word_length, day_of_month, period,
                                    word_1, word_2, word_3
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                                """,
                                (
                                    source.spec.catalogue_id,
                                    source.spec.word_length,
                                    row.day_of_month,
                                    row.period,
                                    row.words[0],
                                    row.words[1],
                                    row.words[2],
                                ),
                            )

                    self._assert_cursor_parity(cursor, sources, expected_state="DRAFT")
                    validate_catalogue_transition("DRAFT", "QUALIFIED")
                    cursor.execute(
                        """
                        UPDATE nexilabs_auth.enigma_catalogue
                        SET catalogue_state = 'QUALIFIED', qualified_at = %s
                        WHERE catalogue_id = ANY(%s)
                          AND catalogue_state = 'DRAFT'
                        """,
                        (when, list(catalogue_ids)),
                    )
                    if cursor.rowcount != len(sources):
                        raise EnigmaDatabaseQualificationError(
                            "not all DRAFT catalogues transitioned to QUALIFIED"
                        )
                    self._assert_cursor_parity(cursor, sources, expected_state="QUALIFIED")

                    validate_catalogue_transition("QUALIFIED", "ACTIVE")
                    cursor.execute(
                        """
                        UPDATE nexilabs_auth.enigma_catalogue
                        SET catalogue_state = 'ACTIVE'
                        WHERE catalogue_id = ANY(%s)
                          AND catalogue_state = 'QUALIFIED'
                        """,
                        (list(catalogue_ids),),
                    )
                    if cursor.rowcount != len(sources):
                        raise EnigmaDatabaseQualificationError(
                            "not all QUALIFIED catalogues transitioned to ACTIVE"
                        )
                    self._assert_cursor_parity(cursor, sources, expected_state="ACTIVE")
                    cursor.execute(
                        """
                        SELECT word_length, COUNT(*)
                        FROM nexilabs_auth.enigma_catalogue
                        WHERE catalogue_state = 'ACTIVE'
                        GROUP BY word_length
                        ORDER BY word_length
                        """
                    )
                    active = [(int(length), int(count)) for length, count in cursor.fetchall()]
                    if active != [(3, 1), (4, 1), (5, 1)]:
                        raise EnigmaDatabaseQualificationError(
                            "one-ACTIVE-catalogue-per-word-length invariant failed"
                        )

        return EnigmaAdmissionReceipt(
            catalogue_count=len(sources),
            entry_count=sum(source.row_count for source in sources),
            active_catalogue_count=len(sources),
            catalogue_ids=catalogue_ids,
        )

    def verify_read_back(
        self,
        sources: tuple[QualifiedEnigmaSource, ...],
    ) -> EnigmaReadBackReceipt:
        catalogue_ids = tuple(source.spec.catalogue_id for source in sources)
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                self._assert_cursor_parity(cursor, sources, expected_state="ACTIVE")
                cursor.execute(
                    """
                    SELECT table_name, column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'nexilabs_auth'
                      AND table_name IN ('enigma_catalogue', 'enigma_catalogue_entry')
                    ORDER BY table_name, ordinal_position
                    """
                )
                column_names = {str(column_name) for _, column_name in cursor.fetchall()}
                forbidden_fragments = ("lookup", "response", "secret", "verifier")
                if any(
                    fragment in column_name.lower()
                    for column_name in column_names
                    for fragment in forbidden_fragments
                ):
                    raise EnigmaDatabaseQualificationError(
                        "shared catalogue storage exposes response-side material"
                    )
                cursor.execute(
                    "SELECT COUNT(*) FROM nexilabs_auth.enigma_catalogue WHERE catalogue_id = ANY(%s)",
                    (list(catalogue_ids),),
                )
                catalogue_count = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT COUNT(*) FROM nexilabs_auth.enigma_catalogue_entry WHERE catalogue_id = ANY(%s)",
                    (list(catalogue_ids),),
                )
                entry_count = int(cursor.fetchone()[0])
        return EnigmaReadBackReceipt(
            catalogue_count=catalogue_count,
            entry_count=entry_count,
            exact_parity=True,
        )

    def qualify_read_adapter(
        self,
        sources: tuple[QualifiedEnigmaSource, ...],
        *,
        profile_id: str = "enigma:profile:qualification:p006-ui-10-2-b",
    ) -> EnigmaAdapterQualificationReceipt:
        from backend.auth.persistence.postgresql_account_authority import PostgreSQLAccountAuthority

        selected_rows = {source.spec.word_length: source.rows[0] for source in sources}
        proven: list[int] = []
        with self.pool.connection(read_only=False) as connection:
            try:
                with connection.transaction():
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO nexilabs_auth.enigma_profile (
                                profile_id, profile_state, activated_at, profile_reference
                            ) VALUES (%s, 'ACTIVE', CURRENT_TIMESTAMP, %s)
                            """,
                            (profile_id, "P006.UI.10.2.B controlled adapter qualification"),
                        )
                        for source in sources:
                            cursor.execute(
                                """
                                INSERT INTO nexilabs_auth.enigma_profile_catalogue (
                                    profile_id, word_length, catalogue_id
                                ) VALUES (%s, %s, %s)
                                """,
                                (profile_id, source.spec.word_length, source.spec.catalogue_id),
                            )

                    adapter = PostgreSQLAccountAuthority(_BorrowedConnectionPool(connection))
                    for source in sources:
                        expected = selected_rows[source.spec.word_length]
                        entry = adapter.enigma_catalogue_entry(
                            profile_id=profile_id,
                            word_length=source.spec.word_length,
                            day_of_month=expected.day_of_month,
                            period=expected.period,
                        )
                        if entry is None:
                            raise EnigmaDatabaseQualificationError(
                                f"PostgreSQL adapter returned no {source.spec.word_length}-letter entry"
                            )
                        if entry.catalogue_id != source.spec.catalogue_id or entry.words != expected.words:
                            raise EnigmaDatabaseQualificationError(
                                f"PostgreSQL adapter parity failed for {source.spec.word_length}-letter catalogue"
                            )
                        proven.append(source.spec.word_length)
                    raise _QualificationRollback()
            except _QualificationRollback:
                pass

        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM nexilabs_auth.enigma_profile WHERE profile_id = %s",
                    (profile_id,),
                )
                profile_count = int(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT COUNT(*) FROM nexilabs_auth.enigma_profile_catalogue WHERE profile_id = %s",
                    (profile_id,),
                )
                binding_count = int(cursor.fetchone()[0])
        cleanup_proven = profile_count == 0 and binding_count == 0
        if not cleanup_proven:
            raise EnigmaDatabaseQualificationError(
                "controlled adapter qualification left persistent profile material"
            )
        return EnigmaAdapterQualificationReceipt(
            profile_id=profile_id,
            qualified_word_lengths=tuple(proven),
            cleanup_proven=cleanup_proven,
        )


__all__ = [
    "EXPECTED_AUTH_TABLES",
    "PostgreSQLEnigmaCatalogueAdmission",
    "validate_catalogue_transition",
]
