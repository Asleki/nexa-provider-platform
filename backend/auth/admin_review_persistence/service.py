"""P006.UI.10.2.C — orchestration for Admin/review persistence qualification."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import (
    AdminReviewAdapterQualificationReceipt,
    AdminReviewQualificationReport,
)
from .qualification import PostgreSQLAdminReviewQualification


@dataclass(frozen=True, slots=True)
class GovernedAdminReviewPersistenceService:
    repository_root: Path
    qualification: PostgreSQLAdminReviewQualification

    def preflight(
        self, *, expected_database: str = "npp_dev"
    ) -> AdminReviewQualificationReport:
        return self.qualification.preflight(
            repository_root=self.repository_root,
            expected_database=expected_database,
        )

    def verify(
        self, *, expected_database: str = "npp_dev"
    ) -> AdminReviewQualificationReport:
        return self.qualification.verify(
            repository_root=self.repository_root,
            expected_database=expected_database,
        )

    def qualify_adapter(
        self, *, expected_database: str = "npp_dev"
    ) -> tuple[
        AdminReviewQualificationReport,
        AdminReviewAdapterQualificationReceipt,
        AdminReviewQualificationReport,
    ]:
        before = self.verify(expected_database=expected_database)
        receipt = self.qualification.qualify_adapter()
        after = self.verify(expected_database=expected_database)
        return before, receipt, after


__all__ = ["GovernedAdminReviewPersistenceService"]
