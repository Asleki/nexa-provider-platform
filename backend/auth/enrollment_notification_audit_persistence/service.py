"""P006.UI.10.2.F — orchestration for enrollment notification/audit persistence qualification."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import (
    EnrollmentNotificationAuditAdapterQualificationReceipt,
    EnrollmentNotificationAuditQualificationReport,
)
from .qualification import PostgreSQLEnrollmentNotificationAuditQualification


@dataclass(frozen=True, slots=True)
class GovernedEnrollmentNotificationAuditPersistenceService:
    """Qualification orchestration only; operational mail/export work is excluded."""

    repository_root: Path
    qualification: PostgreSQLEnrollmentNotificationAuditQualification

    def preflight(
        self, *, expected_database: str = "npp_dev"
    ) -> EnrollmentNotificationAuditQualificationReport:
        return self.qualification.preflight(
            repository_root=self.repository_root,
            expected_database=expected_database,
        )

    def verify(
        self, *, expected_database: str = "npp_dev"
    ) -> EnrollmentNotificationAuditQualificationReport:
        return self.qualification.verify(
            repository_root=self.repository_root,
            expected_database=expected_database,
        )

    def qualify_adapter(
        self, *, expected_database: str = "npp_dev"
    ) -> tuple[
        EnrollmentNotificationAuditQualificationReport,
        EnrollmentNotificationAuditAdapterQualificationReceipt,
        EnrollmentNotificationAuditQualificationReport,
    ]:
        before = self.verify(expected_database=expected_database)
        receipt = self.qualification.qualify_adapter()
        after = self.verify(expected_database=expected_database)
        return before, receipt, after


__all__ = ["GovernedEnrollmentNotificationAuditPersistenceService"]
