from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest

from backend.auth.email_verification_persistence.contracts import EmailVerificationPersistenceError
from backend.auth.email_verification_persistence.postgresql import PostgreSQLEmailVerificationAuthority


NOW = datetime(2026, 9, 6, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 6, 0, 10, tzinfo=timezone.utc)
ROW = (
    "challenge:d:1", "principal:d:1", "email:d:1",
    "keyed-hmac-sha256", 1, "opaque-keyed-verifier-material-not-an-otp",
    "ISSUED", "qualification-v1", NOW, LATER, None, None, 1, 5, 2, NOW,
)


class Cursor:
    def __init__(self, *, one=None, many=None):
        self.one = one
        self.many = [] if many is None else many
        self.calls = []

    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, sql, params=None): self.calls.append((" ".join(str(sql).split()), params))
    def fetchone(self): return self.one
    def fetchall(self): return list(self.many)


class Connection:
    def __init__(self, cursor): self.cursor_obj = cursor
    def cursor(self): return self.cursor_obj


class Pool:
    def __init__(self, cursor): self.cursor_obj = cursor; self.read_only = []
    @contextmanager
    def connection(self, read_only=False):
        self.read_only.append(read_only)
        yield Connection(self.cursor_obj)


def test_challenge_by_id_maps_all_persisted_verifier_lifecycle_and_abuse_fields() -> None:
    cursor = Cursor(one=ROW)
    pool = Pool(cursor)
    record = PostgreSQLEmailVerificationAuthority(pool).challenge_by_id(" challenge:d:1 ")
    assert record is not None
    assert record.challenge_id == "challenge:d:1"
    assert record.otp_verifier_scheme == "keyed-hmac-sha256"
    assert record.otp_verifier_payload == ROW[5]
    assert record.challenge_state == "ISSUED"
    assert record.attempt_count == 1
    assert record.resend_count == 2
    assert pool.read_only == [True]
    assert cursor.calls[0][1] == ("challenge:d:1",)


def test_issued_challenge_is_same_owner_email_bound_and_excludes_revoked_email() -> None:
    cursor = Cursor(many=[ROW])
    authority = PostgreSQLEmailVerificationAuthority(Pool(cursor))
    record = authority.issued_challenge(principal_id="principal:d:1", email_id="email:d:1")
    assert record is not None
    sql, params = cursor.calls[0]
    assert "JOIN nexilabs_auth.account_email AS e" in sql
    assert "e.email_id = c.email_id" in sql
    assert "e.principal_id = c.principal_id" in sql
    assert "e.verification_state <> 'REVOKED'" in sql
    assert "c.challenge_state = 'ISSUED'" in sql
    assert params == ("principal:d:1", "email:d:1")


def test_multiple_issued_rows_fail_closed_even_if_database_uniqueness_drifted() -> None:
    cursor = Cursor(many=[ROW, ROW])
    authority = PostgreSQLEmailVerificationAuthority(Pool(cursor))
    with pytest.raises(EmailVerificationPersistenceError, match="multiple ISSUED"):
        authority.issued_challenge(principal_id="principal:d:1", email_id="email:d:1")


def test_blank_identifiers_do_not_borrow_database_connection() -> None:
    pool = Pool(Cursor())
    authority = PostgreSQLEmailVerificationAuthority(pool)
    assert authority.challenge_by_id("   ") is None
    assert authority.issued_challenge(principal_id="", email_id="email") is None
    assert authority.issued_challenge(principal_id="principal", email_id="  ") is None
    assert pool.read_only == []


def test_adapter_contains_no_write_or_operational_otp_surface() -> None:
    text = __import__("inspect").getsource(PostgreSQLEmailVerificationAuthority)
    upper = text.upper()
    for verb in ("INSERT INTO", "UPDATE ", "DELETE FROM"):
        assert verb not in upper
    assert not hasattr(PostgreSQLEmailVerificationAuthority, "verify_otp")
    assert not hasattr(PostgreSQLEmailVerificationAuthority, "resend")
    assert not hasattr(PostgreSQLEmailVerificationAuthority, "issue")
