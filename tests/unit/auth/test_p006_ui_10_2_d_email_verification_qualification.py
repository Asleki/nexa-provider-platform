from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path

import pytest

from backend.auth.admin_review_persistence.qualification import (
    B_CATALOGUES,
    C_MIGRATION_ID,
    POST_C_AUTH_TABLES,
    REQUIRED_C_COLUMNS,
    REQUIRED_C_CONSTRAINTS,
    REQUIRED_C_FUNCTIONS,
    REQUIRED_C_INDEXES,
    REQUIRED_C_TRIGGERS,
)
from backend.auth.email_verification_persistence.contracts import (
    EmailVerificationQualificationError,
)
from backend.auth.email_verification_persistence.qualification import (
    D_CATALOGUE_VERSION,
    D_FORWARD_FILE,
    D_MIGRATION_ID,
    D_ROLLBACK_FILE,
    D_SEQUENCE,
    POST_D_AUTH_TABLES,
    REQUIRED_D_COLUMNS,
    REQUIRED_D_CONSTRAINTS,
    REQUIRED_D_FUNCTIONS,
    REQUIRED_D_INDEXES,
    REQUIRED_D_TRIGGERS,
    PostgreSQLEmailVerificationQualification,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _manifest_rows(root: Path | None = None) -> list[dict[str, object]]:
    root = root or _repo_root()
    return json.loads(
        (root / "database/migrations/migration_manifest.json").read_text(encoding="utf-8")
    )["migrations"]


def _ledger(rows: list[dict[str, object]], count: int) -> list[tuple[object, ...]]:
    return [
        (
            row["migration_id"],
            row["sequence_number"],
            row["forward_sha256"],
            "APPLIED",
        )
        for row in rows[:count]
    ]


class Cursor:
    def __init__(
        self,
        *,
        ledger_rows: list[tuple[object, ...]],
        tables: tuple[str, ...],
        challenge_count: int = 0,
        authority_count: int = 0,
        missing: str | None = None,
        database: str = "npp_dev",
        tls: bool = True,
    ):
        self.ledger_rows = ledger_rows
        self.tables = tables
        self.challenge_count = challenge_count
        self.authority_count = authority_count
        self.missing = missing
        self.database = database
        self.tls = tls
        self._result: list[tuple[object, ...]] = []

    def __enter__(self): return self
    def __exit__(self, *args): return False

    def execute(self, sql, params=None):
        s = " ".join(str(sql).split())
        if s == "SELECT current_database()":
            self._result = [(self.database,)]
        elif "FROM pg_stat_ssl" in s:
            self._result = [(self.tls,)]
        elif "FROM platform.schema_migration" in s:
            self._result = list(self.ledger_rows)
        elif "FROM information_schema.tables" in s:
            self._result = [(value,) for value in self.tables]
        elif "FROM information_schema.columns" in s:
            table = str(params[0])
            if table == "email_verification_challenge":
                values = set(REQUIRED_D_COLUMNS)
            else:
                values = set(REQUIRED_C_COLUMNS[table])
            if self.missing in values:
                values.remove(self.missing)
            self._result = [(value,) for value in values]
        elif "FROM pg_indexes" in s:
            values = set(REQUIRED_C_INDEXES | REQUIRED_D_INDEXES)
            if self.missing in values:
                values.remove(self.missing)
            self._result = [(value,) for value in values]
        elif "FROM information_schema.table_constraints" in s:
            values = set(REQUIRED_C_CONSTRAINTS | REQUIRED_D_CONSTRAINTS)
            if self.missing in values:
                values.remove(self.missing)
            self._result = [(value,) for value in values]
        elif "FROM information_schema.routines" in s:
            values = set(REQUIRED_C_FUNCTIONS | REQUIRED_D_FUNCTIONS)
            if self.missing in values:
                values.remove(self.missing)
            self._result = [(value,) for value in values]
        elif "FROM information_schema.triggers" in s:
            values = set(REQUIRED_C_TRIGGERS | REQUIRED_D_TRIGGERS)
            if self.missing in values:
                values.remove(self.missing)
            self._result = [(value,) for value in values]
        elif "CROSS JOIN LATERAL aclexplode" in s:
            self._result = [(0,)]
        elif "FROM information_schema.table_privileges" in s:
            self._result = [(0,)]
        elif "FROM information_schema.routine_privileges" in s:
            self._result = [(0,)]
        elif "FROM nexilabs_auth.enigma_catalogue" in s and "COUNT" not in s:
            self._result = list(B_CATALOGUES)
        elif "FROM nexilabs_auth.enigma_catalogue_entry" in s and "GROUP BY" in s:
            self._result = [(3, 93), (4, 93), (5, 93)]
        elif s.startswith("SELECT COUNT(*) FROM nexilabs_auth."):
            table = s.split("FROM nexilabs_auth.", 1)[1].split()[0]
            value = self.challenge_count if table == "email_verification_challenge" else self.authority_count
            self._result = [(value,)]
        else:
            raise AssertionError(f"unexpected SQL: {s}")

    def fetchone(self): return self._result[0]
    def fetchall(self): return list(self._result)


class Connection:
    def __init__(self, cursor): self._cursor = cursor
    def cursor(self): return self._cursor


class Pool:
    def __init__(self, cursor): self.cursor_obj = cursor; self.read_only = []
    @contextmanager
    def connection(self, read_only=False):
        self.read_only.append(read_only)
        yield Connection(self.cursor_obj)


def _successor_root(tmp_path: Path) -> tuple[Path, list[dict[str, object]]]:
    source = _repo_root()
    root = tmp_path / "repo"
    migration_dir = root / "database/migrations"
    migration_dir.mkdir(parents=True)
    for name in (D_FORWARD_FILE, D_ROLLBACK_FILE, "migration_manifest.json"):
        (migration_dir / name).write_bytes((source / "database/migrations" / name).read_bytes())
    path = migration_dir / "migration_manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["catalogue_version"] = max(int(payload["catalogue_version"]), D_CATALOGUE_VERSION) + 1
    next_sequence = len(payload["migrations"]) + 1
    dependency = str(payload["migrations"][-1]["migration_id"])
    payload["migrations"].append({
        "migration_id": "m006_10_02_later_successor",
        "milestone_id": "M006.10.2",
        "sequence_number": next_sequence,
        "description": "later_successor",
        "forward_file": "m006_10_02_later_successor.sql",
        "rollback_file": "m006_10_02_later_successor_rollback.sql",
        "forward_sha256": "a" * 64,
        "rollback_sha256": "b" * 64,
        "forward_byte_size": 1,
        "rollback_byte_size": 1,
        "depends_on": [dependency],
        "transaction_policy": "embedded",
        "expected_objects": {"schemas": [], "tables": [], "indexes": [], "constraints": [], "views": [], "functions": []},
        "destructive": False,
        "catalogue_entry_version": 1,
    })
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return root, payload["migrations"]


def test_repository_artifact_gate_locks_exact_d_row_33_and_hashes() -> None:
    result = PostgreSQLEmailVerificationQualification.verify_repository_artifacts(_repo_root())
    assert len(result) >= D_SEQUENCE
    assert result[31]["migration_id"] == C_MIGRATION_ID
    assert result[32]["migration_id"] == D_MIGRATION_ID
    assert result[32]["sequence_number"] == D_SEQUENCE
    assert result[32]["depends_on"] == [C_MIGRATION_ID]


def test_repository_artifact_gate_is_successor_safe(tmp_path: Path) -> None:
    root, _ = _successor_root(tmp_path)
    result = PostgreSQLEmailVerificationQualification.verify_repository_artifacts(root)
    assert len(result) > D_SEQUENCE
    assert result[32]["migration_id"] == D_MIGRATION_ID


def test_preflight_proves_exact_c_database_predecessor_without_invoking_c_qualifier() -> None:
    rows = _manifest_rows()
    cursor = Cursor(ledger_rows=_ledger(rows, 32), tables=POST_C_AUTH_TABLES)
    result = PostgreSQLEmailVerificationQualification(Pool(cursor)).preflight(
        repository_root=_repo_root()
    )
    assert result.phase == "pre-D"
    assert result.database_migration_count == 32
    assert result.migration_tail_id == C_MIGRATION_ID
    assert result.email_challenge_count == 0


def test_preflight_rejects_non_c_database_tail() -> None:
    rows = _manifest_rows()
    cursor = Cursor(ledger_rows=_ledger(rows, 33), tables=POST_D_AUTH_TABLES)
    with pytest.raises(EmailVerificationQualificationError, match="expected 32"):
        PostgreSQLEmailVerificationQualification(Pool(cursor)).preflight(
            repository_root=_repo_root()
        )


def test_post_d_verify_proves_structure_acl_and_zero_challenge_closure() -> None:
    rows = _manifest_rows()
    pool = Pool(Cursor(ledger_rows=_ledger(rows, 33), tables=POST_D_AUTH_TABLES))
    result = PostgreSQLEmailVerificationQualification(pool).verify(
        repository_root=_repo_root()
    )
    assert result.phase == "post-D"
    assert result.database_migration_count == 33
    assert result.email_challenge_count == 0
    assert result.nexilabs_auth_tables == POST_D_AUTH_TABLES
    assert result.public_schema_privilege_count == 0
    assert result.enigma_catalogue_count == 3
    assert result.enigma_catalogue_entry_count == 279
    assert pool.read_only == [True]


def test_post_d_closure_rejects_seeded_challenge_while_d_is_tail() -> None:
    rows = _manifest_rows()
    cursor = Cursor(
        ledger_rows=_ledger(rows, 33),
        tables=POST_D_AUTH_TABLES,
        challenge_count=1,
    )
    with pytest.raises(EmailVerificationQualificationError, match="zero challenge rows"):
        PostgreSQLEmailVerificationQualification(Pool(cursor)).verify(
            repository_root=_repo_root()
        )


def test_post_d_successor_allows_later_operational_authority_data(tmp_path: Path) -> None:
    root, rows = _successor_root(tmp_path)
    tables = tuple(sorted((*POST_D_AUTH_TABLES, "later_successor_table")))
    cursor = Cursor(
        ledger_rows=_ledger(rows, 34),
        tables=tables,
        challenge_count=7,
        authority_count=2,
    )
    result = PostgreSQLEmailVerificationQualification(Pool(cursor)).verify(
        repository_root=root
    )
    assert result.database_migration_count == 34
    assert result.email_challenge_count == 7
    assert result.principal_count == 2


def test_missing_d_structure_fails_closed() -> None:
    rows = _manifest_rows()
    missing = next(iter(REQUIRED_D_TRIGGERS))
    cursor = Cursor(
        ledger_rows=_ledger(rows, 33),
        tables=POST_D_AUTH_TABLES,
        missing=missing,
    )
    with pytest.raises(EmailVerificationQualificationError, match="missing D triggers"):
        PostgreSQLEmailVerificationQualification(Pool(cursor)).verify(
            repository_root=_repo_root()
        )


def test_wrong_database_and_missing_tls_fail_closed() -> None:
    rows = _manifest_rows()
    with pytest.raises(EmailVerificationQualificationError, match="wrong database target"):
        PostgreSQLEmailVerificationQualification(
            Pool(Cursor(ledger_rows=_ledger(rows, 32), tables=POST_C_AUTH_TABLES, database="wrong"))
        ).preflight(repository_root=_repo_root())
    with pytest.raises(EmailVerificationQualificationError, match="TLS is not active"):
        PostgreSQLEmailVerificationQualification(
            Pool(Cursor(ledger_rows=_ledger(rows, 32), tables=POST_C_AUTH_TABLES, tls=False))
        ).preflight(repository_root=_repo_root())
