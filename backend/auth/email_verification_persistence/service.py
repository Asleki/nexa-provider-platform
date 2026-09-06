"""P006.UI.10.2.D — orchestration for email-verification persistence qualification."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import (
    EmailVerificationAdapterQualificationReceipt,
    EmailVerificationQualificationReport,
)
from .qualification import PostgreSQLEmailVerificationQualification


@dataclass(frozen=True, slots=True)
class GovernedEmailVerificationPersistenceService:
    repository_root: Path
    qualification: PostgreSQLEmailVerificationQualification

    def preflight(
        self, *, expected_database: str = "npp_dev"
    ) -> EmailVerificationQualificationReport:
        return self.qualification.preflight(
            repository_root=self.repository_root,
            expected_database=expected_database,
        )

    def verify(
        self, *, expected_database: str = "npp_dev"
    ) -> EmailVerificationQualificationReport:
        return self.qualification.verify(
            repository_root=self.repository_root,
            expected_database=expected_database,
        )

    def qualify_adapter(
        self, *, expected_database: str = "npp_dev"
    ) -> tuple[
        EmailVerificationQualificationReport,
        EmailVerificationAdapterQualificationReceipt,
        EmailVerificationQualificationReport,
    ]:
        before = self.verify(expected_database=expected_database)
        receipt = self.qualification.qualify_adapter()
        after = self.verify(expected_database=expected_database)
        return before, receipt, after


__all__ = ["GovernedEmailVerificationPersistenceService"]
