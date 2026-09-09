from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.auth.enrollment_notification_audit_persistence.contracts import (
    EnrollmentNotificationAuditAdapterQualificationReceipt,
    EnrollmentNotificationAuditQualificationReport,
)
from verification.auth import p006_ui_10_2_f_enrollment_notification_audit_persistence as cli


def _report(phase: str) -> EnrollmentNotificationAuditQualificationReport:
    return EnrollmentNotificationAuditQualificationReport(
        phase=phase,database_name='npp_dev',tls_active=True,
        repository_migration_count=35,database_migration_count=35,
        migration_tail_sequence=35,migration_tail_id='m006_10_02_enrollment_notification_audit_persistence',
        nexilabs_auth_tables=('audit_export','enrollment_event','notification_delivery'),
        public_schema_privilege_count=0,public_table_privilege_count=0,public_routine_privilege_count=0,
        principal_count=0,credential_count=0,developer_request_count=0,admin_operator_count=0,
        developer_decision_count=0,email_challenge_count=0,enigma_catalogue_count=3,
        enigma_catalogue_entry_count=279,enigma_profile_count=0,principal_enigma_profile_count=0,
        bundle_count=0,bundle_secret_count=0,delivery_count=0,enrollment_event_count=0,
        notification_delivery_count=0,audit_export_count=0,
    )


class Service:
    def preflight(self,*,expected_database): return _report('pre-F')
    def verify(self,*,expected_database): return _report('post-F')
    def qualify_adapter(self,*,expected_database):
        report=_report('post-F')
        receipt=EnrollmentNotificationAuditAdapterQualificationReceipt(
            'request-f',12,'notification-f','NEXILABS_ADMIN_OPERATIONS',
            'audit-export-f','SENT','RETIRED',True,
        )
        return report,receipt,report


class Pool:
    def __init__(self): self.closed=False
    def close(self): self.closed=True


def test_cli_verify_emits_only_persistence_qualification_metadata(monkeypatch,capsys,tmp_path: Path) -> None:
    pool=Pool(); monkeypatch.setattr(cli,'_service',lambda root:(Service(),pool))
    assert cli.main(['verify','--repository-root',str(tmp_path)])==0
    payload=json.loads(capsys.readouterr().out)
    assert payload['milestone']=='P006.UI.10.2.F'
    assert payload['operation']=='verify'
    for key in (
        'migrationWritePerformed','mailRendered','mailSent','mailProviderCredentialPersisted',
        'renderedMailBodyPersisted','auditArtifactGenerated','auditArtifactUploaded',
        'publicAuditUrlActivated','rawCredentialMaterialPersisted',
        'accountActivationOperationPerformed',
    ):
        assert payload[key] is False
    assert payload['database']['enrollmentEventCount']==0
    assert pool.closed is True


def test_cli_adapter_proof_exposes_safe_reference_metadata_only(monkeypatch,capsys,tmp_path: Path) -> None:
    pool=Pool(); monkeypatch.setattr(cli,'_service',lambda root:(Service(),pool))
    assert cli.main(['adapter-proof','--repository-root',str(tmp_path)])==0
    payload=json.loads(capsys.readouterr().out)
    assert payload['syntheticAuthorityRolledBack'] is True
    assert payload['adapter']['eventCount']==12
    assert payload['adapter']['adminAlertRecipientReference']=='NEXILABS_ADMIN_OPERATIONS'
    assert payload['adapter']['notificationState']=='SENT'
    assert payload['adapter']['auditExportState']=='RETIRED'
    rendered=json.dumps(payload).lower()
    for forbidden in (
        'nexatech.core@gmail.com','qualification-f-developer@example.invalid',
        'provider-message:qualification-f','qualification/private/audit-f.pdf',
        'opaque-otp-verifier','opaque-setup-secret-verifier','opaque-delivery-token-verifier',
        'filterreference','objectkey','providermessagereference',
    ):
        assert forbidden not in rendered
    assert pool.closed is True


@pytest.mark.parametrize('command',[
    'send-mail','render-mail','retry-mail','generate-export','upload-export',
    'download-export','activate-account','create-event','record-notification',
])
def test_cli_has_no_operational_mail_export_or_activation_commands(command: str) -> None:
    with pytest.raises(SystemExit):
        cli.main([command])
