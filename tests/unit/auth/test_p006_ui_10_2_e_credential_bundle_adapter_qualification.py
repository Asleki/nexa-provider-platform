from __future__ import annotations

from contextlib import contextmanager

from backend.auth.credential_bundle_persistence import qualification as subject
from backend.auth.credential_bundle_persistence.contracts import (
    CredentialBundleRecord,
    CredentialBundleSecretRecord,
    CredentialDeliveryRecord,
)


class Tx:
    def __init__(self): self.rolled_back = False
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb):
        self.rolled_back = exc_type is not None
        return False


class Cursor:
    def __init__(self): self.calls=[]; self._result=[(0,)]
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def execute(self, sql, params=None):
        text=' '.join(str(sql).split()); self.calls.append((text,params))
        self._result=[(0,)] if text.startswith('SELECT COUNT(*)') else []
    def fetchone(self): return self._result[0]


class Connection:
    def __init__(self): self.cursor_obj=Cursor(); self.tx=Tx()
    def cursor(self): return self.cursor_obj
    def transaction(self): return self.tx


class Pool:
    def __init__(self): self.connection_obj=Connection(); self.read_only=[]
    @contextmanager
    def connection(self,read_only=False):
        self.read_only.append(read_only); yield self.connection_obj


def _bundle() -> CredentialBundleRecord:
    return CredentialBundleRecord(
        bundle_id='bundle:qualification:p006-ui-10-2-e',
        principal_id='principal:qualification:p006-ui-10-2-e',
        enigma_profile_id='enigma-profile:qualification:p006-ui-10-2-e',
        bundle_state='READY', object_provider_code='QUALIFICATION_PRIVATE_OBJECT',
        object_key='qualification/private/bundle-e.zip', content_sha256='a'*64,
        byte_size=4096, created_at='now', integrity_verified_at='now',
        object_confirmed_at='now', ready_at='now', expires_at='later',
        retention_until='much-later', invalidated_at=None, retired_at=None,
    )


def _secret() -> CredentialBundleSecretRecord:
    return CredentialBundleSecretRecord(
        bundle_secret_id='bundle-secret:qualification:p006-ui-10-2-e',
        bundle_id='bundle:qualification:p006-ui-10-2-e',
        escrow_provider_code='QUALIFICATION_KMS_REFERENCE',
        encrypted_secret_reference='opaque-encrypted-secret-reference-qualification-e',
        encryption_context_version='ctx-v1', created_at='now', retired_at=None,
    )


def _delivery(state: str, count: int) -> CredentialDeliveryRecord:
    return CredentialDeliveryRecord(
        delivery_id='delivery:qualification:p006-ui-10-2-e',
        bundle_id='bundle:qualification:p006-ui-10-2-e',
        token_verifier_scheme='qualification-keyed-v1', token_verifier_version=1,
        token_verifier_payload='opaque-delivery-token-verifier-qualification-e',
        delivery_state=state, policy_version='qualification-policy-v1',
        logical_delivery_host_code='CREDENTIAL_DELIVERY_QUALIFICATION',
        issued_at='now', expires_at='later', consumed_at='now' if state=='CONSUMED' else None,
        revoked_at=None, download_count=count,
        first_downloaded_at='now' if count else None,
        last_downloaded_at='now' if count else None,
    )


class FakeAuthority:
    def __init__(self,pool): pass
    def ready_bundle_for_principal(self,principal_id): return _bundle()
    def active_secret_reference(self,bundle_id): return _secret()
    def issued_delivery_for_bundle(self,bundle_id): return _delivery('ISSUED',0)
    def delivery_by_id(self,delivery_id): return _delivery('CONSUMED',1)


def test_adapter_proof_exercises_bundle_secret_delivery_lifecycle_and_rolls_back(monkeypatch) -> None:
    monkeypatch.setattr(subject,'PostgreSQLCredentialBundleAuthority',FakeAuthority)
    pool=Pool()
    receipt=subject.PostgreSQLCredentialBundleQualification(pool).qualify_adapter()
    assert receipt.rollback_verified is True
    assert receipt.bundle_state=='READY'
    assert receipt.delivery_state=='CONSUMED'
    assert pool.connection_obj.tx.rolled_back is True
    sql='\n'.join(statement for statement,_ in pool.connection_obj.cursor_obj.calls)
    assert 'INSERT INTO nexilabs_auth.principal_account' in sql
    assert 'INSERT INTO nexilabs_auth.enigma_profile' in sql
    assert 'INSERT INTO nexilabs_auth.principal_enigma_profile' in sql
    assert 'INSERT INTO nexilabs_auth.credential_bundle' in sql
    assert "bundle_state = 'READY'" in sql
    assert 'INSERT INTO nexilabs_auth.credential_bundle_secret' in sql
    assert 'INSERT INTO nexilabs_auth.credential_delivery' in sql
    assert "delivery_state = 'CONSUMED'" in sql
    assert sql.count('SELECT COUNT(*)')==6
    lowered=sql.lower()
    for forbidden in ('archive_password','raw_token','public_url','presigned_url','s3://','https://'):
        assert forbidden not in lowered
