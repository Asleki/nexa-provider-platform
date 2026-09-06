"""P006.UI.10.2.C — stable records for layered Admin/review persistence reads."""
from __future__ import annotations

from dataclasses import dataclass


ADMIN_PASSWORD_KIND = "ADMIN_PASSWORD"
ADMIN_STATES = ("ACTIVE", "DISABLED")
DEVELOPER_ACCESS_DECISIONS = ("APPROVED", "REJECTED")
DEVELOPER_REJECTION_REASON_CODES = (
    "DUPLICATE_ACTIVE_REQUEST",
    "IDENTITY_NOT_CONFIRMED",
    "ACCESS_ELIGIBILITY_NOT_CONFIRMED",
    "SECURITY_REVIEW_FAILED",
    "PREVIOUS_ACCESS_RESTRICTION",
    "REQUEST_INCOMPLETE",
    "POLICY_REQUIREMENTS_NOT_MET",
)
TECHNICAL_ENROLLMENT_FAILURE_CODES = (
    "INVALID_SETUP",
    "EXPIRED_SETUP",
    "WRONG_OTP",
    "EXPIRED_OTP",
)


class AdminReviewPersistenceError(RuntimeError):
    """Raised when persisted Admin/review authority violates the locked contract."""


class AdminReviewQualificationError(RuntimeError):
    """Raised when PostgreSQL does not match the P006.UI.10.2.C authority contract."""


@dataclass(frozen=True, slots=True)
class AdminOperatorRecord:
    admin_operator_id: str
    principal_id: str
    admin_developer_id: str
    bound_admin_email_id: str
    bound_admin_email: str
    admin_state: str
    created_at: str
    disabled_at: str | None
    bootstrap_reference: str | None
    audit_reference: str


@dataclass(frozen=True, slots=True)
class DeveloperAccessDecisionRecord:
    decision_id: str
    request_id: str
    reviewer_principal_id: str
    admin_operator_id: str
    decision: str
    reason_code: str | None
    safe_explanation: str | None
    internal_reference: str
    policy_version: str
    receipt_reference: str
    decided_at: str


@dataclass(frozen=True, slots=True)
class AdminReviewQualificationReport:
    phase: str
    database_name: str
    tls_active: bool
    repository_migration_count: int
    database_migration_count: int
    migration_tail_sequence: int
    migration_tail_id: str
    nexilabs_auth_tables: tuple[str, ...]
    public_schema_privilege_count: int
    public_table_privilege_count: int
    public_routine_privilege_count: int
    principal_count: int
    credential_count: int
    developer_request_count: int
    admin_operator_count: int
    developer_decision_count: int
    enigma_catalogue_count: int
    enigma_catalogue_entry_count: int
    enigma_profile_count: int
    principal_enigma_profile_count: int

    def safe_summary(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "databaseName": self.database_name,
            "tlsActive": self.tls_active,
            "repositoryMigrationCount": self.repository_migration_count,
            "databaseMigrationCount": self.database_migration_count,
            "migrationTailSequence": self.migration_tail_sequence,
            "migrationTailId": self.migration_tail_id,
            "nexilabsAuthTables": list(self.nexilabs_auth_tables),
            "publicSchemaPrivilegeCount": self.public_schema_privilege_count,
            "publicTablePrivilegeCount": self.public_table_privilege_count,
            "publicRoutinePrivilegeCount": self.public_routine_privilege_count,
            "principalCount": self.principal_count,
            "credentialCount": self.credential_count,
            "developerRequestCount": self.developer_request_count,
            "adminOperatorCount": self.admin_operator_count,
            "developerDecisionCount": self.developer_decision_count,
            "enigmaCatalogueCount": self.enigma_catalogue_count,
            "enigmaCatalogueEntryCount": self.enigma_catalogue_entry_count,
            "enigmaProfileCount": self.enigma_profile_count,
            "principalEnigmaProfileCount": self.principal_enigma_profile_count,
        }


@dataclass(frozen=True, slots=True)
class AdminReviewAdapterQualificationReceipt:
    admin_operator_id: str
    principal_id: str
    admin_password_kind: str
    decision: str
    request_id: str
    rollback_verified: bool

    def safe_summary(self) -> dict[str, object]:
        return {
            "adminOperatorId": self.admin_operator_id,
            "principalId": self.principal_id,
            "adminPasswordKind": self.admin_password_kind,
            "decision": self.decision,
            "requestId": self.request_id,
            "rollbackVerified": self.rollback_verified,
        }


__all__ = [
    "ADMIN_PASSWORD_KIND",
    "ADMIN_STATES",
    "DEVELOPER_ACCESS_DECISIONS",
    "DEVELOPER_REJECTION_REASON_CODES",
    "TECHNICAL_ENROLLMENT_FAILURE_CODES",
    "AdminOperatorRecord",
    "AdminReviewAdapterQualificationReceipt",
    "AdminReviewPersistenceError",
    "AdminReviewQualificationError",
    "AdminReviewQualificationReport",
    "DeveloperAccessDecisionRecord",
]
