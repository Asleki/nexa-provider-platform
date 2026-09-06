from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path

import pytest

from backend.auth.admin_review_persistence.contracts import AdminReviewQualificationError
from backend.auth.admin_review_persistence.qualification import (
    B_CATALOGUES,
    C_CATALOGUE_VERSION,
    C_DEPENDENCY,
    C_FORWARD_FILE,
    C_MIGRATION_ID,
    C_MILESTONE_ID,
    C_ROLLBACK_FILE,
    C_SEQUENCE,
    POST_C_AUTH_TABLES,
    PRE_C_AUTH_TABLES,
    REQUIRED_C_COLUMNS,
    REQUIRED_C_CONSTRAINTS,
    REQUIRED_C_FUNCTIONS,
    REQUIRED_C_INDEXES,
    REQUIRED_C_TRIGGERS,
    PostgreSQLAdminReviewQualification,
)


def _manifest(root: Path) -> list[dict[str, object]]:
    forward = (root / "database/migrations" / C_FORWARD_FILE).read_bytes()
    rollback = (root / "database/migrations" / C_ROLLBACK_FILE).read_bytes()
    rows: list[dict[str, object]] = []
    for seq in range(1, 32):
        rows.append({
            "migration_id": f"historical_{seq}",
            "milestone_id": "historical",
            "sequence_number": seq,
            "forward_sha256": f"{seq:064x}"[-64:],
        })
    rows.append({
        "migration_id": C_MIGRATION_ID,
        "milestone_id": C_MILESTONE_ID,
        "sequence_number": C_SEQUENCE,
        "description": "layered_admin_review_authority",
        "forward_file": C_FORWARD_FILE,
        "rollback_file": C_ROLLBACK_FILE,
        "depends_on": [C_DEPENDENCY],
        "expected_objects": {"schemas": [], "tables": [], "indexes": [], "constraints": [], "views": [], "functions": []},
        "forward_sha256": sha256(forward).hexdigest(),
        "rollback_sha256": sha256(rollback).hexdigest(),
        "forward_byte_size": len(forward),
        "rollback_byte_size": len(rollback),
        "transaction_policy": "embedded",
        "destructive": False,
        "catalogue_entry_version": 1,
    })
    (root / "database/migrations/migration_manifest.json").write_text(
        json.dumps({"manifest_schema": "npp.database-migration-manifest", "manifest_schema_version": 1, "catalogue_version": C_CATALOGUE_VERSION, "migrations": rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    return rows


class Cursor:
    def __init__(self, *, root: Path, post_c: bool, database: str = "npp_dev", tls: bool = True):
        self.rows = _manifest(root)
        self.post_c = post_c
        self.database = database
        self.tls = tls
        self._result = []

    def __enter__(self): return self
    def __exit__(self, *args): return False

    def execute(self, sql, params=None):
        s = " ".join(str(sql).split())
        if s == "SELECT current_database()": self._result = [(self.database,)]
        elif "FROM pg_stat_ssl" in s: self._result = [(self.tls,)]
        elif "FROM platform.schema_migration" in s:
            n = 32 if self.post_c else 31
            self._result = [
                (r["migration_id"], r["sequence_number"], r["forward_sha256"], "APPLIED")
                for r in self.rows[:n]
            ]
        elif "FROM information_schema.tables" in s:
            tables = POST_C_AUTH_TABLES if self.post_c else PRE_C_AUTH_TABLES
            self._result = [(x,) for x in tables]
        elif "CROSS JOIN LATERAL aclexplode" in s: self._result = [(0,)]
        elif "FROM information_schema.table_privileges" in s: self._result = [(0,)]
        elif "FROM information_schema.routine_privileges" in s: self._result = [(0,)]
        elif "FROM nexilabs_auth.enigma_catalogue" in s and "COUNT" not in s:
            self._result = list(B_CATALOGUES)
        elif "FROM nexilabs_auth.enigma_catalogue_entry" in s and "GROUP BY" in s:
            self._result = [(3, 93), (4, 93), (5, 93)]
        elif s.startswith("SELECT COUNT(*) FROM nexilabs_auth."):
            self._result = [(0,)]
        elif "FROM information_schema.columns" in s:
            table = params[0]
            self._result = [(x,) for x in REQUIRED_C_COLUMNS[table]]
        elif "FROM pg_indexes" in s:
            self._result = [(x,) for x in REQUIRED_C_INDEXES]
        elif "FROM information_schema.table_constraints" in s:
            self._result = [(x,) for x in REQUIRED_C_CONSTRAINTS]
        elif "FROM information_schema.routines" in s:
            self._result = [(x,) for x in REQUIRED_C_FUNCTIONS]
        elif "FROM information_schema.triggers" in s:
            self._result = [(x,) for x in REQUIRED_C_TRIGGERS]
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


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    mig = root / "database/migrations"
    mig.mkdir(parents=True)
    source = Path(__file__).resolve().parents[3] / "database/migrations"
    for name in (C_FORWARD_FILE, C_ROLLBACK_FILE):
        (mig / name).write_bytes((source / name).read_bytes())
    return root


def test_repository_artifact_gate_locks_catalogue_16_sequence_32_and_hashes(tmp_path: Path) -> None:
    root = _root(tmp_path)
    rows = _manifest(root)
    result = PostgreSQLAdminReviewQualification.verify_repository_artifacts(root)
    assert len(result) == 32
    assert result[-1]["migration_id"] == C_MIGRATION_ID
    assert result[-1]["sequence_number"] == 32
    assert result[-1]["depends_on"] == [C_DEPENDENCY]


def test_preflight_proves_b_authority_and_zero_user_admin_state_before_c_apply(tmp_path: Path) -> None:
    root = _root(tmp_path)
    cursor = Cursor(root=root, post_c=False)
    report = PostgreSQLAdminReviewQualification(Pool(cursor)).preflight(repository_root=root)
    assert report.phase == "pre-C"
    assert report.database_migration_count == 31
    assert report.migration_tail_sequence == 31
    assert report.admin_operator_count == 0
    assert report.developer_decision_count == 0
    assert report.enigma_catalogue_count == 3
    assert report.enigma_catalogue_entry_count == 279


def test_post_c_verify_proves_structure_acl_zero_seed_and_b_continuity(tmp_path: Path) -> None:
    root = _root(tmp_path)
    cursor = Cursor(root=root, post_c=True)
    report = PostgreSQLAdminReviewQualification(Pool(cursor)).verify(repository_root=root)
    assert report.phase == "post-C"
    assert report.database_migration_count == 32
    assert report.migration_tail_id == C_MIGRATION_ID
    assert report.nexilabs_auth_tables == POST_C_AUTH_TABLES
    assert report.public_schema_privilege_count == 0
    assert report.public_table_privilege_count == 0
    assert report.public_routine_privilege_count == 0
    assert report.principal_count == report.credential_count == report.admin_operator_count == 0
    assert report.developer_request_count == report.developer_decision_count == 0


def test_wrong_database_and_missing_tls_fail_closed(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with pytest.raises(AdminReviewQualificationError, match="wrong database target"):
        PostgreSQLAdminReviewQualification(Pool(Cursor(root=root, post_c=False, database="wrong"))).preflight(repository_root=root)
    with pytest.raises(AdminReviewQualificationError, match="TLS is not active"):
        PostgreSQLAdminReviewQualification(Pool(Cursor(root=root, post_c=False, tls=False))).preflight(repository_root=root)


def test_manifest_hash_drift_is_rejected_before_database_work(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _manifest(root)
    path = root / "database/migrations" / C_FORWARD_FILE
    path.write_text(path.read_text() + "-- drift\n")
    with pytest.raises(AdminReviewQualificationError, match="checksum mismatch"):
        PostgreSQLAdminReviewQualification.verify_repository_artifacts(root)
