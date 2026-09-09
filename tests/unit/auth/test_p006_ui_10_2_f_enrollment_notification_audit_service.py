from __future__ import annotations

from pathlib import Path

from backend.auth.enrollment_notification_audit_persistence.contracts import (
    EnrollmentNotificationAuditAdapterQualificationReceipt,
    EnrollmentNotificationAuditQualificationReport,
)
from backend.auth.enrollment_notification_audit_persistence.service import (
    GovernedEnrollmentNotificationAuditPersistenceService,
)


def _report(phase: str) -> EnrollmentNotificationAuditQualificationReport:
    return EnrollmentNotificationAuditQualificationReport(
        phase=phase, database_name="npp_dev", tls_active=True,
        repository_migration_count=35, database_migration_count=35,
        migration_tail_sequence=35,
        migration_tail_id="m006_10_02_enrollment_notification_audit_persistence",
        nexilabs_auth_tables=("audit_export", "enrollment_event", "notification_delivery"),
        public_schema_privilege_count=0, public_table_privilege_count=0,
        public_routine_privilege_count=0, principal_count=0, credential_count=0,
        developer_request_count=0, admin_operator_count=0, developer_decision_count=0,
        email_challenge_count=0, enigma_catalogue_count=3,
        enigma_catalogue_entry_count=279, enigma_profile_count=0,
        principal_enigma_profile_count=0, bundle_count=0, bundle_secret_count=0,
        delivery_count=0, enrollment_event_count=0, notification_delivery_count=0,
        audit_export_count=0,
    )


class Qualification:
    def __init__(self): self.calls=[]
    def preflight(self, *, repository_root, expected_database):
        self.calls.append(("preflight",repository_root,expected_database)); return _report("pre-F")
    def verify(self, *, repository_root, expected_database):
        self.calls.append(("verify",repository_root,expected_database)); return _report("post-F")
    def qualify_adapter(self):
        self.calls.append(("adapter",))
        return EnrollmentNotificationAuditAdapterQualificationReceipt(
            "request-f", 12, "notification-f", "NEXILABS_ADMIN_OPERATIONS",
            "audit-export-f", "SENT", "RETIRED", True,
        )


def test_service_delegates_preflight_and_verify_to_qualification() -> None:
    q=Qualification(); root=Path("/repo")
    service=GovernedEnrollmentNotificationAuditPersistenceService(root,q)  # type: ignore[arg-type]
    assert service.preflight(expected_database="npp_dev").phase=="pre-F"
    assert service.verify(expected_database="npp_dev").phase=="post-F"
    assert q.calls[:2]==[("preflight",root,"npp_dev"),("verify",root,"npp_dev")]


def test_adapter_proof_is_bracketed_by_post_f_verification() -> None:
    q=Qualification(); root=Path("/repo")
    service=GovernedEnrollmentNotificationAuditPersistenceService(root,q)  # type: ignore[arg-type]
    before,receipt,after=service.qualify_adapter(expected_database="npp_dev")
    assert before.phase==after.phase=="post-F"
    assert receipt.event_count==12 and receipt.rollback_verified is True
    assert receipt.admin_alert_recipient_reference=="NEXILABS_ADMIN_OPERATIONS"
    assert q.calls==[("verify",root,"npp_dev"),("adapter",),("verify",root,"npp_dev")]
