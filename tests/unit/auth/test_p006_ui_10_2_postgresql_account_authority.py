from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest

from backend.auth.contracts import IdentityType, SelectedRuntime
from backend.auth.persistence.postgresql_account_authority import (
    AccountPersistenceError,
    PostgreSQLAccountAuthority,
)


class FakeCursor:
    def __init__(self, plan):
        self.plan = list(plan)
        self.calls = []
        self.current = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement, params):
        self.calls.append((statement, params))
        assert self.plan, "unexpected SQL execution"
        self.current = self.plan.pop(0)

    def fetchone(self):
        value = self.current
        self.current = None
        return value

    def fetchall(self):
        value = self.current
        self.current = None
        return list(value)


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


class FakePool:
    def __init__(self, plan):
        self.cursor = FakeCursor(plan)
        self.read_only_calls = []

    @contextmanager
    def connection(self, read_only=False):
        self.read_only_calls.append(read_only)
        yield FakeConnection(self.cursor)


def test_locked_runtime_contract_still_contains_exactly_two_runtimes() -> None:
    assert {item.value for item in SelectedRuntime} == {"simulation", "production"}


def test_guest_principal_is_runtime_neutral_and_maps_existing_contract() -> None:
    pool = FakePool(
        [
            ("principal:guest:001", "guest_user", "guest"),
            [("public:search",), ("profile:view",)],
        ]
    )
    authority = PostgreSQLAccountAuthority(pool)

    principal = authority.principal_by_username(
        "  Guest_User  ", expected_type=IdentityType.GUEST
    )

    assert principal is not None
    assert principal.principal_id == "principal:guest:001"
    assert principal.username == "guest_user"
    assert principal.identity_type is IdentityType.GUEST
    assert principal.permissions == frozenset({"public:search", "profile:view"})
    assert principal.enigma_profile_id is None
    assert pool.cursor.calls[0][1] == ("guest_user",)
    assert pool.cursor.calls[1][1] == ("principal:guest:001",)
    assert pool.read_only_calls == [True]
    assert all("runtime" not in statement.lower() for statement, _ in pool.cursor.calls)


def test_developer_principal_requires_one_active_enigma_profile() -> None:
    pool = FakePool(
        [
            ("principal:developer:001", "dev_user", "nexadevs_developer"),
            [("registry:view",)],
            [],
        ]
    )
    authority = PostgreSQLAccountAuthority(pool)

    assert authority.principal_by_username(
        "dev_user", expected_type=IdentityType.NEXADEVS_DEVELOPER
    ) is None

    duplicate_pool = FakePool(
        [
            ("principal:developer:001", "dev_user", "nexadevs_developer"),
            [],
            [("enigma:profile:1",), ("enigma:profile:2",)],
        ]
    )
    with pytest.raises(AccountPersistenceError, match="multiple active Enigma profile"):
        PostgreSQLAccountAuthority(duplicate_pool).principal_by_username("dev_user")


def test_developer_principal_maps_active_enigma_profile_without_authenticating_password() -> None:
    pool = FakePool(
        [
            ("principal:developer:002", "dev_user", "nexadevs_developer"),
            [("registry:view",), ("simulation:event:create",)],
            [("enigma:profile:production:002",)],
        ]
    )
    principal = PostgreSQLAccountAuthority(pool).principal_by_username("DEV_USER")

    assert principal is not None
    assert principal.identity_type is IdentityType.NEXADEVS_DEVELOPER
    assert principal.enigma_profile_id == "enigma:profile:production:002"
    assert principal.permissions == frozenset(
        {"registry:view", "simulation:event:create"}
    )
    assert all("verifier_payload" not in statement for statement, _ in pool.cursor.calls)


def test_active_password_verifier_is_returned_as_opaque_persistence_record() -> None:
    opaque = "pbkdf2_sha256$210000$opaque-salt$opaque-digest"
    pool = FakePool(
        [[("cred:001", "principal:guest:001", "password", "pbkdf2_sha256", 1, opaque)]]
    )
    record = PostgreSQLAccountAuthority(pool).active_password_verifier(
        "principal:guest:001"
    )

    assert record is not None
    assert record.verifier_scheme == "pbkdf2_sha256"
    assert record.verifier_version == 1
    assert record.verifier_payload == opaque
    assert pool.cursor.calls[0][1] == ("principal:guest:001",)


def test_duplicate_active_password_rows_are_rejected_as_authority_corruption() -> None:
    pool = FakePool(
        [[
            ("cred:001", "principal:guest:001", "password", "a", 1, "x" * 20),
            ("cred:002", "principal:guest:001", "password", "a", 1, "y" * 20),
        ]]
    )
    with pytest.raises(AccountPersistenceError, match="multiple active password credential"):
        PostgreSQLAccountAuthority(pool).active_password_verifier("principal:guest:001")


def test_primary_email_and_developer_setup_are_persistence_only_records() -> None:
    verified_at = datetime(2026, 9, 5, 8, 0, tzinfo=timezone.utc)
    email_pool = FakePool(
        [[("email:001", "principal:guest:001", "guest@example.test", "VERIFIED", verified_at)]]
    )
    email = PostgreSQLAccountAuthority(email_pool).primary_email("principal:guest:001")
    assert email is not None
    assert email.verification_state == "VERIFIED"
    assert email.verified_at == verified_at.isoformat()

    issued_at = datetime(2026, 9, 5, 8, 0, tzinfo=timezone.utc)
    expires_at = datetime(2026, 9, 6, 8, 0, tzinfo=timezone.utc)
    setup_pool = FakePool(
        [(
            "setup:public:001",
            "request:001",
            "lookup:v1:opaque-key-001",
            "argon2id",
            1,
            "opaque-verifier-payload-value",
            "ISSUED",
            issued_at,
            expires_at,
            None,
            None,
            None,
        )]
    )
    setup = PostgreSQLAccountAuthority(setup_pool).developer_setup_by_lookup_key("lookup:v1:opaque-key-001")
    assert setup is not None
    assert setup.setup_lookup_key == "lookup:v1:opaque-key-001"
    assert setup.verifier_scheme == "argon2id"
    assert setup.verifier_payload == "opaque-verifier-payload-value"
    assert setup.setup_state == "ISSUED"
    assert setup.issued_at == issued_at.isoformat()
    assert setup.expires_at == expires_at.isoformat()


def test_enigma_catalogue_read_keeps_catalogue_profile_and_assignment_separate() -> None:
    pool = FakePool(
        [(
            "catalogue:3:v1",
            "profile:developer:001",
            3,
            5,
            "Morning",
            "ARC",
            "BAY",
            "CUE",
        )]
    )
    entry = PostgreSQLAccountAuthority(pool).enigma_catalogue_entry(
        profile_id="profile:developer:001",
        word_length=3,
        day_of_month=5,
        period="morning",
    )

    assert entry is not None
    assert entry.catalogue_id == "catalogue:3:v1"
    assert entry.profile_id == "profile:developer:001"
    assert entry.words == ("ARC", "BAY", "CUE")
    assert pool.cursor.calls[0][1] == (
        "profile:developer:001",
        3,
        5,
        "Morning",
    )

    with pytest.raises(ValueError):
        PostgreSQLAccountAuthority(FakePool([])).enigma_catalogue_entry(
            profile_id="p", word_length=6, day_of_month=1, period="Morning"
        )
