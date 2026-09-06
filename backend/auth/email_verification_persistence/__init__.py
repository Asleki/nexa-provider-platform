"""P006.UI.10.2.D governed email-verification challenge persistence."""
from .contracts import (
    EMAIL_VERIFICATION_CHALLENGE_STATES,
    TERMINAL_EMAIL_VERIFICATION_CHALLENGE_STATES,
    EmailVerificationAdapterQualificationReceipt,
    EmailVerificationChallengePolicy,
    EmailVerificationChallengeRecord,
    EmailVerificationPersistenceError,
    EmailVerificationQualificationError,
    EmailVerificationQualificationReport,
)
from .postgresql import PostgreSQLEmailVerificationAuthority
from .qualification import PostgreSQLEmailVerificationQualification
from .service import GovernedEmailVerificationPersistenceService

__all__ = [
    "EMAIL_VERIFICATION_CHALLENGE_STATES",
    "TERMINAL_EMAIL_VERIFICATION_CHALLENGE_STATES",
    "EmailVerificationAdapterQualificationReceipt",
    "EmailVerificationChallengePolicy",
    "EmailVerificationChallengeRecord",
    "EmailVerificationPersistenceError",
    "EmailVerificationQualificationError",
    "EmailVerificationQualificationReport",
    "GovernedEmailVerificationPersistenceService",
    "PostgreSQLEmailVerificationAuthority",
    "PostgreSQLEmailVerificationQualification",
]
