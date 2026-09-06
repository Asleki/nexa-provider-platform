from __future__ import annotations

from pathlib import Path

from backend.auth.email_verification_persistence.contracts import (
    EmailVerificationAdapterQualificationReceipt,
    EmailVerificationQualificationReport,
)
from backend.auth.email_verification_persistence.service import GovernedEmailVerificationPersistenceService


def _report(phase: str) -> EmailVerificationQualificationReport:
    return EmailVerificationQualificationReport(
        phase=phase,
        database_name="npp_dev",
        tls_active=True,
        repository_migration_count=33,
        database_migration_count=33,
        migration_tail_sequence=33,
        migration_tail_id="m006_10_02_email_verification_challenge",
        nexilabs_auth_tables=("email_verification_challenge",),
        public_schema_privilege_count=0,
        public_table_privilege_count=0,
        public_routine_privilege_count=0,
        principal_count=0,
        credential_count=0,
        developer_request_count=0,
        admin_operator_count=0,
        developer_decision_count=0,
        email_challenge_count=0,
        enigma_catalogue_count=3,
        enigma_catalogue_entry_count=279,
        enigma_profile_count=0,
        principal_enigma_profile_count=0,
    )


class Qualification:
    def __init__(self): self.calls = []
    def preflight(self, *, repository_root, expected_database):
        self.calls.append(("preflight", repository_root, expected_database))
        return _report("pre-D")
    def verify(self, *, repository_root, expected_database):
        self.calls.append(("verify", repository_root, expected_database))
        return _report("post-D")
    def qualify_adapter(self):
        self.calls.append(("adapter",))
        return EmailVerificationAdapterQualificationReceipt(
            "challenge:d", "principal:d", "email:d", "LOCKED",
            "keyed-hmac-sha256", True,
        )


def test_service_delegates_preflight_and_verify_to_one_qualification_boundary(tmp_path: Path) -> None:
    qualification = Qualification()
    service = GovernedEmailVerificationPersistenceService(tmp_path, qualification)
    assert service.preflight().phase == "pre-D"
    assert service.verify().phase == "post-D"
    assert qualification.calls[:2] == [
        ("preflight", tmp_path, "npp_dev"),
        ("verify", tmp_path, "npp_dev"),
    ]


def test_service_adapter_proof_is_bracketed_by_post_d_verification(tmp_path: Path) -> None:
    qualification = Qualification()
    service = GovernedEmailVerificationPersistenceService(tmp_path, qualification)
    before, receipt, after = service.qualify_adapter()
    assert before.phase == after.phase == "post-D"
    assert receipt.rollback_verified is True
    assert qualification.calls == [
        ("verify", tmp_path, "npp_dev"),
        ("adapter",),
        ("verify", tmp_path, "npp_dev"),
    ]
