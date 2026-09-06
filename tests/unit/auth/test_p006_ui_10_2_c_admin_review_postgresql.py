from contextlib import contextmanager
from datetime import datetime, timezone

import pytest

from backend.auth.admin_review_persistence.contracts import AdminReviewPersistenceError
from backend.auth.admin_review_persistence.postgresql import PostgreSQLAdminReviewAuthority


class FakeCursor:
    def __init__(self, plan):
        self.plan = list(plan)
        self.current = None
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement, params):
        self.calls.append((" ".join(str(statement).split()), params))
        assert self.plan, "unexpected SQL execution"
        self.current = self.plan.pop(0)

    def fetchall(self):
        current = self.current
        self.current = None
        return list(current or [])


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_object = cursor

    def cursor(self):
        return self.cursor_object


class FakePool:
    def __init__(self, plan):
        self.cursor = FakeCursor(plan)
        self.read_only_calls = []

    @contextmanager
    def connection(self, read_only=False):
        self.read_only_calls.append(read_only)
        yield FakeConnection(self.cursor)


def _operator_row():
    now = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)
    return (
        "operator:001",
        "principal:001",
        "ADMIN-DESIGNATED-ID-001",
        "email:001",
        "admin@example.test",
        "ACTIVE",
        now,
        None,
        None,
        "audit:001",
    )


def test_active_admin_operator_is_effective_server_side_authority_read() -> None:
    pool = FakePool([[_operator_row()]])
    record = PostgreSQLAdminReviewAuthority(pool).active_admin_operator("principal:001")
    assert record is not None
    assert record.admin_operator_id == "operator:001"
    assert record.principal_id == "principal:001"
    assert record.bound_admin_email == "admin@example.test"
    statement, params = pool.cursor.calls[0]
    assert "p.identity_type = 'nexadevs_developer'" in statement
    assert "p.account_state = 'ACTIVE'" in statement
    assert "e.verification_state = 'VERIFIED'" in statement
    assert "ao.admin_state = 'ACTIVE'" in statement
    assert params == ("principal:001",)
    assert pool.read_only_calls == [True]


def test_admin_designated_developer_id_lookup_is_database_canonicalized_not_prefix_based() -> None:
    pool = FakePool([[_operator_row()]])
    record = PostgreSQLAdminReviewAuthority(pool).active_admin_operator_by_developer_id(
        "  admin-designated-id-001  "
    )
    assert record is not None
    statement, params = pool.cursor.calls[0]
    assert "lower(btrim(%s))" in statement
    assert "DEV-" not in statement
    assert params == ("admin-designated-id-001",)


def test_admin_password_verifier_uses_distinct_credential_kind() -> None:
    opaque = "qualification-admin-verifier-payload"
    pool = FakePool([[("credential:admin:001", "principal:001", "ADMIN_PASSWORD", "argon2id", 1, opaque)]])
    record = PostgreSQLAdminReviewAuthority(pool).active_admin_password_verifier("principal:001")
    assert record is not None
    assert record.credential_kind == "ADMIN_PASSWORD"
    assert record.verifier_payload == opaque
    statement, _ = pool.cursor.calls[0]
    assert "credential_kind = 'ADMIN_PASSWORD'" in statement
    assert "credential_kind = 'password'" not in statement


def test_duplicate_admin_password_rows_are_rejected_as_authority_corruption() -> None:
    rows = [
        ("credential:1", "principal:001", "ADMIN_PASSWORD", "x", 1, "a" * 20),
        ("credential:2", "principal:001", "ADMIN_PASSWORD", "x", 1, "b" * 20),
    ]
    with pytest.raises(AdminReviewPersistenceError, match="multiple active ADMIN_PASSWORD"):
        PostgreSQLAdminReviewAuthority(FakePool([rows])).active_admin_password_verifier("principal:001")


def test_developer_access_decision_maps_immutable_reviewer_evidence() -> None:
    decided = datetime(2026, 9, 6, 12, 5, tzinfo=timezone.utc)
    pool = FakePool([[(
        "decision:001",
        "request:001",
        "principal:001",
        "operator:001",
        "REJECTED",
        "REQUEST_INCOMPLETE",
        "Please complete the request.",
        "internal:001",
        "policy-v1",
        "receipt:001",
        decided,
    )]])
    record = PostgreSQLAdminReviewAuthority(pool).developer_access_decision("request:001")
    assert record is not None
    assert record.reviewer_principal_id == "principal:001"
    assert record.admin_operator_id == "operator:001"
    assert record.decision == "REJECTED"
    assert record.reason_code == "REQUEST_INCOMPLETE"
    assert record.receipt_reference == "receipt:001"
    assert record.decided_at == decided.isoformat()
