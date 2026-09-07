from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import inspect

import pytest

from backend.auth.credential_bundle_persistence.contracts import CredentialBundlePersistenceError
from backend.auth.credential_bundle_persistence.postgresql import PostgreSQLCredentialBundleAuthority


NOW = datetime(2026, 9, 6, 20, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 7, 20, 0, tzinfo=timezone.utc)
RETENTION = datetime(2026, 10, 6, 20, 0, tzinfo=timezone.utc)
BUNDLE_ROW = (
    "bundle-1", "principal-1", "profile-1", "READY", "AWS_S3_PRIVATE",
    "private/credentials/bundle-1.zip", "a" * 64, 4096,
    NOW, NOW, NOW, NOW, LATER, RETENTION, None, None,
)
SECRET_ROW = (
    "bundle-secret-1", "bundle-1", "AWS_KMS_REFERENCE",
    "kms:opaque:reference", "ctx-v1", NOW, None,
)
DELIVERY_ROW = (
    "delivery-1", "bundle-1", "hmac-sha256", 1, "v" * 64,
    "ISSUED", "delivery-policy-v1", "CREDENTIAL_DELIVERY_SECURE",
    NOW, LATER, None, None, 0, None, None,
)


class Cursor:
    def __init__(self, *, one=None, many=None):
        self.one = one
        self.many = [] if many is None else list(many)
        self.calls: list[tuple[str, object]] = []

    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, sql, params=None): self.calls.append((" ".join(str(sql).split()), params))
    def fetchone(self): return self.one
    def fetchall(self): return list(self.many)


class Connection:
    def __init__(self, cursor): self.cursor_obj = cursor
    def cursor(self): return self.cursor_obj


class Pool:
    def __init__(self, cursor): self.cursor_obj = cursor; self.read_only: list[bool] = []
    @contextmanager
    def connection(self, read_only=False):
        self.read_only.append(read_only)
        yield Connection(self.cursor_obj)


def test_bundle_by_id_maps_integrity_object_and_retention_metadata() -> None:
    cursor = Cursor(one=BUNDLE_ROW)
    pool = Pool(cursor)
    record = PostgreSQLCredentialBundleAuthority(pool).bundle_by_id(" bundle-1 ")
    assert record is not None
    assert record.bundle_state == "READY"
    assert record.object_key == "private/credentials/bundle-1.zip"
    assert record.content_sha256 == "a" * 64
    assert record.byte_size == 4096
    assert record.retention_until == RETENTION.isoformat()
    assert pool.read_only == [True]
    assert cursor.calls[0][1] == ("bundle-1",)


def test_ready_bundle_for_principal_is_developer_active_profile_same_owner_bound() -> None:
    cursor = Cursor(many=[BUNDLE_ROW])
    authority = PostgreSQLCredentialBundleAuthority(Pool(cursor))
    record = authority.ready_bundle_for_principal("principal-1")
    assert record is not None
    sql, params = cursor.calls[0]
    assert "p.identity_type = 'nexadevs_developer'" in sql
    assert "ep.profile_state = 'ACTIVE'" in sql
    assert "pep.principal_id = b.principal_id" in sql
    assert "pep.profile_id = b.enigma_profile_id" in sql
    assert "pep.assignment_state = 'ACTIVE'" in sql
    assert "b.bundle_state = 'READY'" in sql
    assert "p.account_state = 'ACTIVE'" not in sql
    assert params == ("principal-1",)


def test_active_secret_reference_maps_opaque_reference_without_decryption() -> None:
    cursor = Cursor(many=[SECRET_ROW])
    authority = PostgreSQLCredentialBundleAuthority(Pool(cursor))
    record = authority.active_secret_reference("bundle-1")
    assert record is not None
    assert record.encrypted_secret_reference == "kms:opaque:reference"
    assert record.encryption_context_version == "ctx-v1"
    sql, _ = cursor.calls[0]
    assert "s.retired_at IS NULL" in sql


def test_issued_delivery_requires_ready_bundle_and_maps_download_accounting() -> None:
    cursor = Cursor(many=[DELIVERY_ROW])
    authority = PostgreSQLCredentialBundleAuthority(Pool(cursor))
    record = authority.issued_delivery_for_bundle("bundle-1")
    assert record is not None
    assert record.token_verifier_payload == "v" * 64
    assert record.download_count == 0
    sql, params = cursor.calls[0]
    assert "JOIN nexilabs_auth.credential_bundle AS b" in sql
    assert "b.bundle_state = 'READY'" in sql
    assert "d.delivery_state = 'ISSUED'" in sql
    assert params == ("bundle-1",)


def test_delivery_by_id_reads_durable_terminal_or_issued_history_by_primary_key() -> None:
    cursor = Cursor(one=DELIVERY_ROW)
    record = PostgreSQLCredentialBundleAuthority(Pool(cursor)).delivery_by_id("delivery-1")
    assert record is not None
    assert record.delivery_id == "delivery-1"


@pytest.mark.parametrize("method,args", [
    ("ready_bundle_for_principal", ("principal-1",)),
    ("active_secret_reference", ("bundle-1",)),
    ("issued_delivery_for_bundle", ("bundle-1",)),
])
def test_duplicate_current_rows_fail_closed(method: str, args: tuple[str, ...]) -> None:
    rows = [BUNDLE_ROW, BUNDLE_ROW]
    if method == "active_secret_reference": rows = [SECRET_ROW, SECRET_ROW]
    if method == "issued_delivery_for_bundle": rows = [DELIVERY_ROW, DELIVERY_ROW]
    authority = PostgreSQLCredentialBundleAuthority(Pool(Cursor(many=rows)))
    with pytest.raises(CredentialBundlePersistenceError, match="multiple active"):
        getattr(authority, method)(*args)


def test_blank_identifiers_do_not_borrow_database_connection() -> None:
    pool = Pool(Cursor())
    authority = PostgreSQLCredentialBundleAuthority(pool)
    assert authority.bundle_by_id(" ") is None
    assert authority.ready_bundle_for_principal("") is None
    assert authority.active_secret_reference("\t") is None
    assert authority.delivery_by_id(" ") is None
    assert authority.issued_delivery_for_bundle("\n") is None
    assert pool.read_only == []


def test_adapter_contains_no_write_cloud_crypto_token_mail_or_activation_surface() -> None:
    text = inspect.getsource(PostgreSQLCredentialBundleAuthority)
    upper = text.upper()
    for verb in ("INSERT INTO", "UPDATE ", "DELETE FROM"):
        assert verb not in upper
    for name in (
        "upload", "encrypt", "decrypt", "presign", "mint_token", "verify_token",
        "send_mail", "activate_account", "increment_download",
    ):
        assert not hasattr(PostgreSQLCredentialBundleAuthority, name)
