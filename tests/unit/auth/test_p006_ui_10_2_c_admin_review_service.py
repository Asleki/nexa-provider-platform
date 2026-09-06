from pathlib import Path

from backend.auth.admin_review_persistence.contracts import (
    AdminReviewAdapterQualificationReceipt,
    AdminReviewQualificationReport,
)
from backend.auth.admin_review_persistence.service import GovernedAdminReviewPersistenceService


def _report(phase: str) -> AdminReviewQualificationReport:
    return AdminReviewQualificationReport(
        phase=phase,
        database_name="npp_dev",
        tls_active=True,
        repository_migration_count=32,
        database_migration_count=32 if phase == "verify" else 31,
        migration_tail_sequence=32 if phase == "verify" else 31,
        migration_tail_id=(
            "m006_10_02_layered_admin_review_authority"
            if phase == "verify"
            else "m006_10_02_nexilabs_account_credential_authority"
        ),
        nexilabs_auth_tables=(),
        public_schema_privilege_count=0,
        public_table_privilege_count=0,
        public_routine_privilege_count=0,
        principal_count=0,
        credential_count=0,
        developer_request_count=0,
        admin_operator_count=0,
        developer_decision_count=0,
        enigma_catalogue_count=3,
        enigma_catalogue_entry_count=279,
        enigma_profile_count=0,
        principal_enigma_profile_count=0,
    )


class FakeQualification:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def preflight(self, *, repository_root: Path, expected_database: str):
        self.calls.append(("preflight", repository_root, expected_database))
        return _report("preflight")

    def verify(self, *, repository_root: Path, expected_database: str):
        self.calls.append(("verify", repository_root, expected_database))
        return _report("verify")

    def qualify_adapter(self):
        self.calls.append(("qualify_adapter",))
        return AdminReviewAdapterQualificationReceipt(
            admin_operator_id="qualification:admin-operator",
            principal_id="qualification:principal",
            admin_password_kind="ADMIN_PASSWORD",
            decision="APPROVED",
            request_id="qualification:request",
            rollback_verified=True,
        )


def test_preflight_delegates_with_repository_root_and_database_boundary() -> None:
    qualification = FakeQualification()
    root = Path("/repo")
    service = GovernedAdminReviewPersistenceService(root, qualification)  # type: ignore[arg-type]

    report = service.preflight(expected_database="npp_dev")

    assert report.phase == "preflight"
    assert qualification.calls == [("preflight", root, "npp_dev")]


def test_verify_delegates_without_writing_or_changing_runtime_semantics() -> None:
    qualification = FakeQualification()
    root = Path("/repo")
    service = GovernedAdminReviewPersistenceService(root, qualification)  # type: ignore[arg-type]

    report = service.verify(expected_database="npp_dev")

    assert report.phase == "verify"
    assert qualification.calls == [("verify", root, "npp_dev")]


def test_adapter_qualification_is_bracketed_by_post_migration_verification() -> None:
    qualification = FakeQualification()
    root = Path("/repo")
    service = GovernedAdminReviewPersistenceService(root, qualification)  # type: ignore[arg-type]

    before, receipt, after = service.qualify_adapter(expected_database="npp_dev")

    assert before.phase == "verify"
    assert after.phase == "verify"
    assert receipt.admin_password_kind == "ADMIN_PASSWORD"
    assert receipt.rollback_verified is True
    assert qualification.calls == [
        ("verify", root, "npp_dev"),
        ("qualify_adapter",),
        ("verify", root, "npp_dev"),
    ]
