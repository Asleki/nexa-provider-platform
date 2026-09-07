"""P006.UI.10.2.E — orchestration for bundle/storage/delivery persistence qualification."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import (
    CredentialBundleAdapterQualificationReceipt,
    CredentialBundleQualificationReport,
)
from .qualification import PostgreSQLCredentialBundleQualification


@dataclass(frozen=True, slots=True)
class GovernedCredentialBundlePersistenceService:
    repository_root: Path
    qualification: PostgreSQLCredentialBundleQualification

    def preflight(self, *, expected_database: str = "npp_dev") -> CredentialBundleQualificationReport:
        return self.qualification.preflight(
            repository_root=self.repository_root,
            expected_database=expected_database,
        )

    def verify(self, *, expected_database: str = "npp_dev") -> CredentialBundleQualificationReport:
        return self.qualification.verify(
            repository_root=self.repository_root,
            expected_database=expected_database,
        )

    def qualify_adapter(self, *, expected_database: str = "npp_dev") -> tuple[
        CredentialBundleQualificationReport,
        CredentialBundleAdapterQualificationReceipt,
        CredentialBundleQualificationReport,
    ]:
        before = self.verify(expected_database=expected_database)
        receipt = self.qualification.qualify_adapter()
        after = self.verify(expected_database=expected_database)
        return before, receipt, after


__all__ = ["GovernedCredentialBundlePersistenceService"]
