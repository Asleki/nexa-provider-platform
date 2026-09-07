from __future__ import annotations

from pathlib import Path

from backend.auth.credential_bundle_persistence.contracts import (
    CredentialBundleAdapterQualificationReceipt,
    CredentialBundleQualificationReport,
)
from backend.auth.credential_bundle_persistence.service import GovernedCredentialBundlePersistenceService


def _report(phase: str) -> CredentialBundleQualificationReport:
    return CredentialBundleQualificationReport(
        phase=phase, database_name="npp_dev", tls_active=True,
        repository_migration_count=34, database_migration_count=34,
        migration_tail_sequence=34, migration_tail_id="m006_10_02_credential_bundle_storage_delivery",
        nexilabs_auth_tables=("credential_bundle","credential_bundle_secret","credential_delivery"),
        public_schema_privilege_count=0, public_table_privilege_count=0,
        public_routine_privilege_count=0, principal_count=0, credential_count=0,
        developer_request_count=0, admin_operator_count=0, developer_decision_count=0,
        email_challenge_count=0, enigma_catalogue_count=3, enigma_catalogue_entry_count=279,
        enigma_profile_count=0, principal_enigma_profile_count=0,
        bundle_count=0, bundle_secret_count=0, delivery_count=0,
    )


class Qualification:
    def __init__(self): self.calls=[]
    def preflight(self, *, repository_root, expected_database):
        self.calls.append(("preflight",repository_root,expected_database)); return _report("pre-E")
    def verify(self, *, repository_root, expected_database):
        self.calls.append(("verify",repository_root,expected_database)); return _report("post-E")
    def qualify_adapter(self):
        self.calls.append(("adapter",))
        return CredentialBundleAdapterQualificationReceipt(
            "bundle-e","principal-e","profile-e","secret-e","delivery-e","READY","CONSUMED",True
        )


def test_service_delegates_preflight_and_verify_to_qualification() -> None:
    q=Qualification(); root=Path("/repo")
    service=GovernedCredentialBundlePersistenceService(root,q)  # type: ignore[arg-type]
    assert service.preflight(expected_database="npp_dev").phase=="pre-E"
    assert service.verify(expected_database="npp_dev").phase=="post-E"
    assert q.calls[:2]==[("preflight",root,"npp_dev"),("verify",root,"npp_dev")]


def test_adapter_proof_is_bracketed_by_post_e_verification() -> None:
    q=Qualification(); root=Path("/repo")
    service=GovernedCredentialBundlePersistenceService(root,q)  # type: ignore[arg-type]
    before,receipt,after=service.qualify_adapter(expected_database="npp_dev")
    assert before.phase==after.phase=="post-E"
    assert receipt.rollback_verified is True
    assert q.calls==[("verify",root,"npp_dev"),("adapter",),("verify",root,"npp_dev")]
