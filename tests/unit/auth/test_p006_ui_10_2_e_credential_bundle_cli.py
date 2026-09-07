from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.auth.credential_bundle_persistence.contracts import (
    CredentialBundleAdapterQualificationReceipt,
    CredentialBundleQualificationReport,
)
from verification.auth import p006_ui_10_2_e_credential_bundle_storage_delivery as cli


def _report(phase: str) -> CredentialBundleQualificationReport:
    return CredentialBundleQualificationReport(
        phase=phase,database_name='npp_dev',tls_active=True,
        repository_migration_count=34,database_migration_count=34,
        migration_tail_sequence=34,migration_tail_id='m006_10_02_credential_bundle_storage_delivery',
        nexilabs_auth_tables=('credential_bundle','credential_bundle_secret','credential_delivery'),
        public_schema_privilege_count=0,public_table_privilege_count=0,public_routine_privilege_count=0,
        principal_count=0,credential_count=0,developer_request_count=0,admin_operator_count=0,
        developer_decision_count=0,email_challenge_count=0,enigma_catalogue_count=3,
        enigma_catalogue_entry_count=279,enigma_profile_count=0,principal_enigma_profile_count=0,
        bundle_count=0,bundle_secret_count=0,delivery_count=0,
    )


class Service:
    def preflight(self,*,expected_database): return _report('pre-E')
    def verify(self,*,expected_database): return _report('post-E')
    def qualify_adapter(self,*,expected_database):
        report=_report('post-E')
        receipt=CredentialBundleAdapterQualificationReceipt(
            'bundle-e','principal-e','profile-e','secret-e','delivery-e','READY','CONSUMED',True
        )
        return report,receipt,report


class Pool:
    def __init__(self): self.closed=False
    def close(self): self.closed=True


def test_cli_verify_emits_only_persistence_qualification_metadata(monkeypatch,capsys,tmp_path: Path) -> None:
    pool=Pool(); monkeypatch.setattr(cli,'_service',lambda root:(Service(),pool))
    assert cli.main(['verify','--repository-root',str(tmp_path)])==0
    payload=json.loads(capsys.readouterr().out)
    assert payload['milestone']=='P006.UI.10.2.E'
    assert payload['operation']=='verify'
    for key in (
        'migrationWritePerformed','bundleGenerated','objectUploadPerformed','kmsOperationPerformed',
        'deliveryTokenIssued','rawDeliveryTokenPersisted','archivePasswordPersisted',
        'publicCredentialUrlActivated','mailSent','accountActivated',
    ):
        assert payload[key] is False
    assert pool.closed is True


def test_cli_adapter_proof_emits_no_private_object_token_or_secret_material(monkeypatch,capsys,tmp_path: Path) -> None:
    pool=Pool(); monkeypatch.setattr(cli,'_service',lambda root:(Service(),pool))
    assert cli.main(['adapter-proof','--repository-root',str(tmp_path)])==0
    payload=json.loads(capsys.readouterr().out)
    assert payload['syntheticAuthorityRolledBack'] is True
    assert payload['adapter']['bundleState']=='READY'
    assert payload['adapter']['deliveryState']=='CONSUMED'
    rendered=json.dumps(payload).lower()
    for forbidden in ('objectkey','encryptedsecretreference','tokenverifierpayload',
                      'qualification/private/bundle', 'opaque-encrypted-secret',
                      'opaque-delivery-token-verifier'):
        assert forbidden not in rendered
    assert payload['archivePasswordPersisted'] is False
    assert payload['rawDeliveryTokenPersisted'] is False
    assert pool.closed is True


@pytest.mark.parametrize('command',[
    'generate-bundle','upload','encrypt','decrypt','issue-token','verify-token',
    'send-mail','download','activate-account',
])
def test_cli_has_no_operational_bundle_delivery_commands(command: str) -> None:
    with pytest.raises(SystemExit):
        cli.main([command])
