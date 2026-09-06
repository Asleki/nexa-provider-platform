"""P006.UI.10.2.D — stable records for email-verification challenge persistence."""
from __future__ import annotations

from dataclasses import dataclass


EMAIL_VERIFICATION_CHALLENGE_STATES = (
    "ISSUED",
    "VERIFIED",
    "EXPIRED",
    "LOCKED",
    "INVALIDATED",
)
TERMINAL_EMAIL_VERIFICATION_CHALLENGE_STATES = (
    "VERIFIED",
    "EXPIRED",
    "LOCKED",
    "INVALIDATED",
)


class EmailVerificationPersistenceError(RuntimeError):
    """Raised when persisted email-verification authority violates its contract."""


class EmailVerificationQualificationError(RuntimeError):
    """Raised when PostgreSQL does not match the P006.UI.10.2.D authority."""


@dataclass(frozen=True, slots=True)
class EmailVerificationChallengePolicy:
    """Server-side OTP policy configuration; no browser-owned policy constants."""

    policy_version: str
    otp_lifetime_seconds: int
    max_attempts: int
    resend_delay_seconds: int

    def __post_init__(self) -> None:
        if not isinstance(self.policy_version, str) or not self.policy_version.strip():
            raise ValueError("policy_version must be non-blank text")
        if len(self.policy_version.strip()) > 255:
            raise ValueError("policy_version must be at most 255 characters")
        for name in ("otp_lifetime_seconds", "max_attempts", "resend_delay_seconds"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    def safe_summary(self) -> dict[str, object]:
        return {
            "policyVersion": self.policy_version.strip(),
            "otpLifetimeSeconds": self.otp_lifetime_seconds,
            "maxAttempts": self.max_attempts,
            "resendDelaySeconds": self.resend_delay_seconds,
        }


@dataclass(frozen=True, slots=True)
class EmailVerificationChallengeRecord:
    challenge_id: str
    principal_id: str
    email_id: str
    otp_verifier_scheme: str
    otp_verifier_version: int
    otp_verifier_payload: str
    challenge_state: str
    policy_version: str
    issued_at: str
    expires_at: str
    consumed_at: str | None
    invalidated_at: str | None
    attempt_count: int
    max_attempts: int
    resend_count: int
    last_resend_at: str | None

    def safe_summary(self) -> dict[str, object]:
        """Return non-secret diagnostics; verifier payload is intentionally excluded."""
        return {
            "challengeId": self.challenge_id,
            "principalId": self.principal_id,
            "emailId": self.email_id,
            "otpVerifierScheme": self.otp_verifier_scheme,
            "otpVerifierVersion": self.otp_verifier_version,
            "challengeState": self.challenge_state,
            "policyVersion": self.policy_version,
            "issuedAt": self.issued_at,
            "expiresAt": self.expires_at,
            "consumedAt": self.consumed_at,
            "invalidatedAt": self.invalidated_at,
            "attemptCount": self.attempt_count,
            "maxAttempts": self.max_attempts,
            "resendCount": self.resend_count,
            "lastResendAt": self.last_resend_at,
        }


@dataclass(frozen=True, slots=True)
class EmailVerificationQualificationReport:
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
    email_challenge_count: int
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
            "emailChallengeCount": self.email_challenge_count,
            "enigmaCatalogueCount": self.enigma_catalogue_count,
            "enigmaCatalogueEntryCount": self.enigma_catalogue_entry_count,
            "enigmaProfileCount": self.enigma_profile_count,
            "principalEnigmaProfileCount": self.principal_enigma_profile_count,
        }


@dataclass(frozen=True, slots=True)
class EmailVerificationAdapterQualificationReceipt:
    challenge_id: str
    principal_id: str
    email_id: str
    challenge_state: str
    verifier_scheme: str
    rollback_verified: bool

    def safe_summary(self) -> dict[str, object]:
        return {
            "challengeId": self.challenge_id,
            "principalId": self.principal_id,
            "emailId": self.email_id,
            "challengeState": self.challenge_state,
            "verifierScheme": self.verifier_scheme,
            "rollbackVerified": self.rollback_verified,
        }


__all__ = [
    "EMAIL_VERIFICATION_CHALLENGE_STATES",
    "TERMINAL_EMAIL_VERIFICATION_CHALLENGE_STATES",
    "EmailVerificationAdapterQualificationReceipt",
    "EmailVerificationChallengePolicy",
    "EmailVerificationChallengeRecord",
    "EmailVerificationPersistenceError",
    "EmailVerificationQualificationError",
    "EmailVerificationQualificationReport",
]
