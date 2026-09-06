from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path

import pytest

from backend.auth.enigma_catalogue_admission.contracts import EnigmaDatabaseQualificationError
from backend.auth.enigma_catalogue_admission.postgresql import (
    EXPECTED_AUTH_TABLES,
    PostgreSQLEnigmaCatalogueAdmission,
)


class PlannedCursor:
    def __init__(self, plan):
        self.plan = list(plan)
        self.current = None
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement, params=None):
        self.calls.append((" ".join(str(statement).split()), params))
        assert self.plan, "unexpected SQL execution"
        self.current = self.plan.pop(0)

    def fetchone(self):
        if isinstance(self.current, list):
            return self.current[0] if self.current else None
        return self.current

    def fetchall(self):
        return list(self.current or [])


class PlannedConnection:
    def __init__(self, plan):
        self.cursor_object = PlannedCursor(plan)

    def cursor(self):
        return self.cursor_object


class PlannedPool:
    def __init__(self, plan):
        self.connection_object = PlannedConnection(plan)
        self.read_only_calls = []

    @contextmanager
    def connection(self, read_only=False):
        self.read_only_calls.append(read_only)
        yield self.connection_object


def _manifest(tmp_path: Path, checksum: str = "a" * 64) -> Path:
    path = tmp_path / "migration_manifest.json"
    path.write_text(
        json.dumps(
            {
                "manifest_schema": "npp.database-migration-manifest",
                "manifest_schema_version": 1,
                "catalogue_version": 15,
                "migrations": [
                    {
                        "migration_id": "m_test",
                        "sequence_number": 1,
                        "forward_sha256": checksum,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _plan(*, database="npp_dev", tls=True, checksum="a" * 64, status="APPLIED", counts=(0, 0, 0, 0, 0)):
    return [
        (database,),
        (tls,),
        [("m_test", 1, checksum, status)],
        [(name,) for name in EXPECTED_AUTH_TABLES],
        (0,),
        (0,),
        *((value,) for value in counts),
    ]


def test_preflight_proves_target_tls_ledger_schema_acl_and_empty_authority(tmp_path: Path) -> None:
    pool = PlannedPool(_plan())
    report = PostgreSQLEnigmaCatalogueAdmission(pool).preflight(
        manifest_path=_manifest(tmp_path),
        expected_database="npp_dev",
        require_empty_catalogue_authority=True,
    )

    assert report.database_name == "npp_dev"
    assert report.tls_active is True
    assert report.repository_migration_count == 1
    assert report.database_migration_count == 1
    assert report.migration_tail_sequence == 1
    assert report.migration_tail_id == "m_test"
    assert report.nexilabs_auth_tables == EXPECTED_AUTH_TABLES
    assert report.public_schema_privilege_count == 0
    assert report.public_table_privilege_count == 0
    assert pool.read_only_calls == [True]


@pytest.mark.parametrize(
    "plan,match",
    [
        (_plan(database="wrong"), "wrong database target"),
        (_plan(tls=False), "TLS is not active"),
        (_plan(checksum="b" * 64), "checksum mismatch"),
        (_plan(status="FAILED"), "not APPLIED"),
    ],
)
def test_preflight_rejects_wrong_target_tls_or_ledger(plan, match: str, tmp_path: Path) -> None:
    with pytest.raises(EnigmaDatabaseQualificationError, match=match):
        PostgreSQLEnigmaCatalogueAdmission(PlannedPool(plan)).preflight(
            manifest_path=_manifest(tmp_path),
            expected_database="npp_dev",
        )


def test_preflight_rejects_nonempty_initial_catalogue_or_real_principal_state(tmp_path: Path) -> None:
    # counts = principal, catalogue, entry, profile, principal_profile_assignment
    for counts in ((1, 0, 0, 0, 0), (0, 1, 93, 0, 0), (0, 0, 0, 1, 0), (0, 0, 0, 0, 1)):
        with pytest.raises(EnigmaDatabaseQualificationError):
            PostgreSQLEnigmaCatalogueAdmission(PlannedPool(_plan(counts=counts))).preflight(
                manifest_path=_manifest(tmp_path),
                expected_database="npp_dev",
                require_empty_catalogue_authority=True,
            )
