from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import re

import pytest

from backend.auth.enigma_catalogue_admission.contracts import (
    EnigmaDatabaseQualificationError,
    EnigmaSourceSpec,
)
from backend.auth.enigma_catalogue_admission.postgresql import (
    PostgreSQLEnigmaCatalogueAdmission,
    validate_catalogue_transition,
)
from backend.auth.enigma_catalogue_admission.source import EXPECTED_HEADER, qualify_source_bytes


def _word(index: int, length: int, salt: int = 0) -> str:
    value = index + salt
    chars = []
    for _ in range(length):
        chars.append(chr(ord("A") + value % 26))
        value //= 26
    return "".join(reversed(chars))


def _qualified(length: int):
    lines = [",".join(EXPECTED_HEADER)]
    index = 0
    for day in range(1, 32):
        for period in ("Morning", "Noon", "Evening"):
            words = (_word(index, length), _word(index, length, 1000), _word(index, length, 2000))
            lines.append(f"{day},{period},{words[0]},{words[1]},{words[2]},TOKEN{length}_{index}")
            index += 1
    raw = ("\n".join(lines) + "\n").encode("ascii")
    path = Path(f"development/auth/private/enigma/enigma_words_{length}.csv")
    spec = EnigmaSourceSpec(
        length,
        path,
        path.as_posix(),
        sha256(raw).hexdigest(),
        f"enigma:catalogue:test:{length}:v1",
    )
    return qualify_source_bytes(spec, raw)


class FakeTransaction:
    def __init__(self, connection):
        self.connection = connection
        self.snapshot = None

    def __enter__(self):
        self.snapshot = deepcopy(self.connection.state)
        self.connection.transaction_entries += 1
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.connection.state = self.snapshot
            self.connection.rollbacks += 1
        else:
            self.connection.commits += 1
        return False


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.current = None
        self.rowcount = -1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def fetchone(self):
        if isinstance(self.current, list):
            return self.current[0] if self.current else None
        return self.current

    def fetchall(self):
        if self.current is None:
            return []
        return list(self.current)

    def execute(self, statement, params=None):
        sql = " ".join(str(statement).split())
        self.connection.calls.append((sql, params))
        self.rowcount = -1
        state = self.connection.state

        if sql.startswith("SELECT catalogue_id, word_length, catalogue_version, catalogue_state FROM nexilabs_auth.enigma_catalogue"):
            self.current = [
                (cid, row["word_length"], row["version"], row["state"])
                for cid, row in state["catalogues"].items()
                if row["word_length"] in (3, 4, 5)
            ]
            return
        if sql == "SELECT COUNT(*) FROM nexilabs_auth.enigma_catalogue_entry":
            self.current = (len(state["entries"]),)
            return
        if sql.startswith("INSERT INTO nexilabs_auth.enigma_catalogue ("):
            cid, length, version, source_reference, source_sha = params
            state["catalogues"][cid] = {
                "word_length": int(length),
                "version": int(version),
                "state": "DRAFT",
                "source_reference": str(source_reference),
                "source_sha": str(source_sha),
            }
            self.rowcount = 1
            return
        if sql.startswith("INSERT INTO nexilabs_auth.enigma_catalogue_entry ("):
            self.connection.entry_insert_attempts += 1
            if self.connection.fail_after_entry is not None and self.connection.entry_insert_attempts > self.connection.fail_after_entry:
                raise RuntimeError("synthetic transaction failure")
            cid, length, day, period, w1, w2, w3 = params
            state["entries"][(cid, int(day), str(period))] = (int(length), str(w1), str(w2), str(w3))
            self.rowcount = 1
            return
        if sql.startswith("SELECT catalogue_id, word_length, catalogue_version, catalogue_state, source_reference, source_sha256 FROM nexilabs_auth.enigma_catalogue"):
            ids = set(params[0])
            rows = []
            for cid, row in state["catalogues"].items():
                if cid in ids:
                    rows.append((cid, row["word_length"], row["version"], row["state"], row["source_reference"], row["source_sha"]))
            self.current = sorted(rows, key=lambda x: x[1])
            return
        if sql.startswith("SELECT catalogue_id, word_length, day_of_month, period, word_1, word_2, word_3 FROM nexilabs_auth.enigma_catalogue_entry"):
            ids = set(params[0])
            period_order = {"Morning": 0, "Noon": 1, "Evening": 2}
            rows = [
                (cid, value[0], day, period, value[1], value[2], value[3])
                for (cid, day, period), value in state["entries"].items()
                if cid in ids
            ]
            self.current = sorted(rows, key=lambda x: (x[1], x[2], period_order[x[3]]))
            return
        if sql.startswith("UPDATE nexilabs_auth.enigma_catalogue SET catalogue_state = 'QUALIFIED'"):
            ids = set(params[1])
            count = 0
            for cid in ids:
                row = state["catalogues"].get(cid)
                if row and row["state"] == "DRAFT":
                    row["state"] = "QUALIFIED"
                    count += 1
            self.rowcount = count
            return
        if sql.startswith("UPDATE nexilabs_auth.enigma_catalogue SET catalogue_state = 'ACTIVE'"):
            ids = set(params[0])
            count = 0
            for cid in ids:
                row = state["catalogues"].get(cid)
                if row and row["state"] == "QUALIFIED":
                    row["state"] = "ACTIVE"
                    count += 1
            self.rowcount = count
            return
        if sql.startswith("SELECT word_length, COUNT(*) FROM nexilabs_auth.enigma_catalogue WHERE catalogue_state = 'ACTIVE'"):
            counts = {}
            for row in state["catalogues"].values():
                if row["state"] == "ACTIVE":
                    counts[row["word_length"]] = counts.get(row["word_length"], 0) + 1
            self.current = sorted(counts.items())
            return
        if sql.startswith("SELECT table_name, column_name FROM information_schema.columns"):
            self.current = [("enigma_catalogue", name) for name in self.connection.catalogue_columns]
            self.current += [("enigma_catalogue_entry", name) for name in self.connection.entry_columns]
            return
        if sql.startswith("SELECT COUNT(*) FROM nexilabs_auth.enigma_catalogue WHERE catalogue_id = ANY"):
            ids = set(params[0])
            self.current = (sum(1 for cid in state["catalogues"] if cid in ids),)
            return
        if sql.startswith("SELECT COUNT(*) FROM nexilabs_auth.enigma_catalogue_entry WHERE catalogue_id = ANY"):
            ids = set(params[0])
            self.current = (sum(1 for cid, _, _ in state["entries"] if cid in ids),)
            return
        raise AssertionError(f"unexpected SQL: {sql}")


class FakeConnection:
    def __init__(self, *, fail_after_entry=None):
        self.state = {"catalogues": {}, "entries": {}}
        self.calls = []
        self.fail_after_entry = fail_after_entry
        self.entry_insert_attempts = 0
        self.transaction_entries = 0
        self.commits = 0
        self.rollbacks = 0
        self.catalogue_columns = (
            "catalogue_id", "word_length", "catalogue_version", "catalogue_state",
            "source_reference", "source_sha256", "created_at", "qualified_at", "retired_at",
        )
        self.entry_columns = (
            "catalogue_id", "word_length", "day_of_month", "period", "word_1", "word_2", "word_3",
        )

    def cursor(self):
        return FakeCursor(self)

    def transaction(self):
        return FakeTransaction(self)


class FakePool:
    def __init__(self, connection):
        self.connection_object = connection
        self.read_only_calls = []

    @contextmanager
    def connection(self, read_only=False):
        self.read_only_calls.append(read_only)
        yield self.connection_object


def test_transactional_admission_creates_three_active_catalogues_and_279_shared_rows() -> None:
    sources = tuple(_qualified(length) for length in (3, 4, 5))
    connection = FakeConnection()
    authority = PostgreSQLEnigmaCatalogueAdmission(FakePool(connection))

    receipt = authority.admit(sources)

    assert receipt.catalogue_count == 3
    assert receipt.entry_count == 279
    assert receipt.active_catalogue_count == 3
    assert len(connection.state["catalogues"]) == 3
    assert len(connection.state["entries"]) == 279
    assert {row["state"] for row in connection.state["catalogues"].values()} == {"ACTIVE"}
    assert connection.commits == 1
    assert connection.rollbacks == 0


def test_transaction_failure_rolls_back_every_catalogue_and_entry() -> None:
    sources = tuple(_qualified(length) for length in (3, 4, 5))
    connection = FakeConnection(fail_after_entry=50)
    authority = PostgreSQLEnigmaCatalogueAdmission(FakePool(connection))

    with pytest.raises(RuntimeError, match="synthetic transaction failure"):
        authority.admit(sources)

    assert connection.state["catalogues"] == {}
    assert connection.state["entries"] == {}
    assert connection.commits == 0
    assert connection.rollbacks == 1


def test_existing_history_is_never_silently_mutated_by_initial_v1_admission() -> None:
    sources = tuple(_qualified(length) for length in (3, 4, 5))
    connection = FakeConnection()
    authority = PostgreSQLEnigmaCatalogueAdmission(FakePool(connection))
    authority.admit(sources)
    snapshot = deepcopy(connection.state)

    with pytest.raises(EnigmaDatabaseQualificationError, match="refuses to mutate/overwrite"):
        authority.admit(sources)

    assert connection.state == snapshot


def test_read_back_proves_shared_parity_and_forbids_response_side_columns() -> None:
    sources = tuple(_qualified(length) for length in (3, 4, 5))
    connection = FakeConnection()
    authority = PostgreSQLEnigmaCatalogueAdmission(FakePool(connection))
    authority.admit(sources)

    receipt = authority.verify_read_back(sources)
    assert receipt.catalogue_count == 3
    assert receipt.entry_count == 279
    assert receipt.exact_parity is True

    connection.entry_columns = (*connection.entry_columns, "profile_lookup_word")
    with pytest.raises(EnigmaDatabaseQualificationError, match="response-side material"):
        authority.verify_read_back(sources)


def test_catalogue_lifecycle_is_forward_only_and_requires_future_retirement_not_mutation() -> None:
    validate_catalogue_transition("DRAFT", "QUALIFIED")
    validate_catalogue_transition("QUALIFIED", "ACTIVE")
    validate_catalogue_transition("ACTIVE", "RETIRED")

    for current, target in (
        ("DRAFT", "ACTIVE"),
        ("ACTIVE", "QUALIFIED"),
        ("RETIRED", "ACTIVE"),
        ("ACTIVE", "ACTIVE"),
    ):
        with pytest.raises(EnigmaDatabaseQualificationError):
            validate_catalogue_transition(current, target)


def test_service_source_failure_happens_before_any_database_preflight_or_write(monkeypatch, tmp_path: Path) -> None:
    from backend.auth.enigma_catalogue_admission.contracts import EnigmaSourceQualificationError
    from backend.auth.enigma_catalogue_admission.service import GovernedEnigmaCatalogueService

    class DatabaseMustNotBeTouched:
        def __getattr__(self, name):
            raise AssertionError(f"database was touched after source failure: {name}")

    def fail_sources(*args, **kwargs):
        raise EnigmaSourceQualificationError("synthetic malformed source")

    monkeypatch.setattr(
        "backend.auth.enigma_catalogue_admission.service.qualify_all_sources",
        fail_sources,
    )
    service = GovernedEnigmaCatalogueService(tmp_path, DatabaseMustNotBeTouched())
    with pytest.raises(EnigmaSourceQualificationError, match="malformed source"):
        service.admit()


def test_service_closure_gate_requires_exact_three_catalogues_279_entries_and_zero_user_profile_state() -> None:
    from backend.auth.enigma_catalogue_admission.contracts import PostgreSQLPreflightReport
    from backend.auth.enigma_catalogue_admission.service import GovernedEnigmaCatalogueService

    base = dict(
        database_name="npp_dev",
        tls_active=True,
        repository_migration_count=31,
        database_migration_count=31,
        migration_tail_sequence=31,
        migration_tail_id="m006_10_02_nexilabs_account_credential_authority",
        nexilabs_auth_tables=(),
        public_schema_privilege_count=0,
        public_table_privilege_count=0,
        principal_count=0,
        catalogue_count=3,
        catalogue_entry_count=279,
        profile_count=0,
        principal_profile_assignment_count=0,
    )
    GovernedEnigmaCatalogueService._assert_b_closure_counts(PostgreSQLPreflightReport(**base))

    wrong = dict(base)
    wrong["profile_count"] = 1
    with pytest.raises(RuntimeError, match="closure counts"):
        GovernedEnigmaCatalogueService._assert_b_closure_counts(PostgreSQLPreflightReport(**wrong))
