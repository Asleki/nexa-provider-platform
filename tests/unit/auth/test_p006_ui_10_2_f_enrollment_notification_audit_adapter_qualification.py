from __future__ import annotations

from contextlib import contextmanager

from backend.auth.enrollment_notification_audit_persistence import qualification as subject
from backend.auth.enrollment_notification_audit_persistence.contracts import (
    ADMIN_OPERATIONS_RECIPIENT_REFERENCE,
    AuditExportRecord,
    EnrollmentEventRecord,
    EVENT_AUTHORITY_TYPES,
    NotificationDeliveryRecord,
)


class Tx:
    def __init__(self): self.rolled_back=False
    def __enter__(self): return self
    def __exit__(self,exc_type,exc,tb):
        self.rolled_back=exc_type is not None
        return False


class Cursor:
    def __init__(self): self.calls=[]; self._result=[(0,)]
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def execute(self,sql,params=None):
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


def _event(event_type: str, index: int) -> EnrollmentEventRecord:
    authority_type=EVENT_AUTHORITY_TYPES[event_type]
    return EnrollmentEventRecord(
        event_id=f'event-{index}', request_id='developer-request:qualification:p006-ui-10-2-f:approved',
        event_type=event_type, authority_type=authority_type,
        authority_id=f'authority-{index}', occurred_at='now', source_reference=f'receipt:event-{index}',
        correlation_id='correlation:qualification-f', causation_event_id=None,
    )


def _notification(notification_id: str, state: str) -> NotificationDeliveryRecord:
    failed=state=='FAILED'; sent=state=='SENT'
    return NotificationDeliveryRecord(
        notification_id=notification_id, event_id='event-1',
        template_code='ADMIN_DEVELOPER_REQUEST_ALERT' if sent else 'DEVELOPER_REQUEST_APPROVED',
        template_version=1,
        recipient_reference=ADMIN_OPERATIONS_RECIPIENT_REFERENCE if sent else 'DEVELOPER_ACCESS_REQUEST:request-f',
        provider_message_reference='provider-message:qualification-f' if sent else None,
        delivery_state=state, queued_at='now', sent_at='now' if sent else None,
        failed_at='now' if failed else None,
        failure_code='QUALIFICATION_PROVIDER_FAILURE' if failed else None,
    )


def _audit(state: str) -> AuditExportRecord:
    return AuditExportRecord(
        export_id='audit-export:qualification:p006-ui-10-2-f',
        requested_by_admin_operator_id='admin-operator:qualification:p006-ui-10-2-f',
        report_type='DEVELOPER_ENROLLMENT_AUDIT', filter_reference='AUDIT_FILTER:qualification-f',
        object_provider_code='QUALIFICATION_PRIVATE_OBJECT',
        object_key='qualification/private/audit-f.pdf', content_sha256='b'*64, byte_size=8192,
        export_state=state, generated_at='now', expires_at='later', retention_until='much-later',
        expired_at='later' if state in {'EXPIRED','RETIRED'} else None,
        retired_at='much-later' if state=='RETIRED' else None,
    )


class FakeAuthority:
    audit_calls=0
    def __init__(self,pool): self.pool=pool
    def events_for_request(self,request_id):
        approved=(
            'REQUEST_RECEIVED','UNDER_REVIEW','APPROVED','SETUP_ISSUED','SETUP_VERIFIED',
            'OTP_ISSUED','EMAIL_VERIFIED','ENIGMA_PROVISIONED','BUNDLE_READY',
            'DELIVERY_ISSUED','ACCOUNT_ACTIVATED',
        )
        return tuple(_event(event_type,i) for i,event_type in enumerate(approved,1))
    def notification_by_id(self,notification_id):
        return _notification(notification_id,'FAILED' if notification_id.endswith(':failed') else 'SENT')
    def audit_export_by_id(self,export_id):
        type(self).audit_calls+=1
        return _audit('AVAILABLE' if type(self).audit_calls==1 else 'RETIRED')


def test_adapter_proof_covers_all_f_event_types_notification_states_audit_retention_and_rolls_back(monkeypatch) -> None:
    FakeAuthority.audit_calls=0
    monkeypatch.setattr(subject,'PostgreSQLEnrollmentNotificationAuditAuthority',FakeAuthority)
    pool=Pool()
    receipt=subject.PostgreSQLEnrollmentNotificationAuditQualification(pool).qualify_adapter()
    assert receipt.event_count==12
    assert receipt.notification_state=='SENT'
    assert receipt.admin_alert_recipient_reference==ADMIN_OPERATIONS_RECIPIENT_REFERENCE
    assert receipt.audit_export_state=='RETIRED'
    assert receipt.rollback_verified is True
    assert pool.read_only==[False]
    assert pool.connection_obj.tx.rolled_back is True

    calls=pool.connection_obj.cursor_obj.calls
    event_inserts=[params for sql,params in calls if sql.startswith('INSERT INTO nexilabs_auth.enrollment_event')]
    assert len(event_inserts)==12
    assert {params[2] for params in event_inserts}=={
        'REQUEST_RECEIVED','UNDER_REVIEW','APPROVED','REJECTED','SETUP_ISSUED','SETUP_VERIFIED',
        'OTP_ISSUED','EMAIL_VERIFIED','ENIGMA_PROVISIONED','BUNDLE_READY','DELIVERY_ISSUED',
        'ACCOUNT_ACTIVATED',
    }
    joined='\n'.join(sql for sql,_ in calls)
    assert "'ADMIN_DEVELOPER_REQUEST_ALERT'" in joined
    assert "delivery_state='FAILED'" in joined
    assert "export_state='EXPIRED'" in joined and "export_state='RETIRED'" in joined
    assert "UPDATE nexilabs_auth.principal_account SET account_state='ACTIVE', updated_at=CURRENT_TIMESTAMP" in joined


def test_adapter_proof_uses_only_synthetic_opaque_secret_verifiers_and_never_persists_mail_body(monkeypatch) -> None:
    FakeAuthority.audit_calls=0
    monkeypatch.setattr(subject,'PostgreSQLEnrollmentNotificationAuditAuthority',FakeAuthority)
    pool=Pool(); subject.PostgreSQLEnrollmentNotificationAuditQualification(pool).qualify_adapter()
    joined='\n'.join(sql for sql,_ in pool.connection_obj.cursor_obj.calls).lower()
    for forbidden in ('message_body','rendered_body','html_body','text_body','provider_api_key','smtp_password','public_url','presigned_url'):
        assert forbidden not in joined
    # Predecessor verifier fields are deliberately populated only with opaque synthetic verifier material.
    flattened=' '.join(repr(params) for _,params in pool.connection_obj.cursor_obj.calls if params is not None).lower()
    assert 'opaque-setup-secret-verifier-qualification-f' in flattened
    assert 'opaque-otp-verifier-payload-qualification-f' in flattened
    assert 'opaque-delivery-token-verifier-qualification-f' in flattened
