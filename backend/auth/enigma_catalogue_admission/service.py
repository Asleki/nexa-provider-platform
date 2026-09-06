"""P006.UI.10.2.B — Orchestration for source qualification and governed admission."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import (
    EnigmaAdapterQualificationReceipt,
    EnigmaAdmissionReceipt,
    EnigmaReadBackReceipt,
    PostgreSQLPreflightReport,
    QualifiedEnigmaSource,
)
from .postgresql import PostgreSQLEnigmaCatalogueAdmission
from .source import DEFAULT_SOURCE_SPECS, qualify_all_sources


@dataclass(frozen=True, slots=True)
class GovernedEnigmaCatalogueService:
    repository_root: Path
    database: PostgreSQLEnigmaCatalogueAdmission | None = None

    def qualify_sources(self) -> tuple[QualifiedEnigmaSource, ...]:
        return qualify_all_sources(self.repository_root, DEFAULT_SOURCE_SPECS)

    def preflight(
        self,
        *,
        expected_database: str = "npp_dev",
        require_empty_catalogue_authority: bool = False,
    ) -> PostgreSQLPreflightReport:
        if self.database is None:
            raise RuntimeError("PostgreSQL admission authority is required for database preflight")
        return self.database.preflight(
            manifest_path=self.repository_root / "database" / "migrations" / "migration_manifest.json",
            expected_database=expected_database,
            require_empty_catalogue_authority=require_empty_catalogue_authority,
        )

    @staticmethod
    def _assert_b_closure_counts(report: PostgreSQLPreflightReport) -> None:
        expected = {
            "principal": 0,
            "catalogue": 3,
            "catalogue_entry": 279,
            "profile": 0,
            "principal_profile_assignment": 0,
        }
        actual = {
            "principal": report.principal_count,
            "catalogue": report.catalogue_count,
            "catalogue_entry": report.catalogue_entry_count,
            "profile": report.profile_count,
            "principal_profile_assignment": report.principal_profile_assignment_count,
        }
        if actual != expected:
            raise RuntimeError(
                f"P006.UI.10.2.B closure counts differ from governed target: {actual}"
            )

    def admit(
        self,
        *,
        expected_database: str = "npp_dev",
    ) -> tuple[
        tuple[QualifiedEnigmaSource, ...],
        PostgreSQLPreflightReport,
        EnigmaAdmissionReceipt,
        EnigmaReadBackReceipt,
        PostgreSQLPreflightReport,
    ]:
        """Qualify every private source before opening the database admission path."""
        sources = self.qualify_sources()
        if self.database is None:
            raise RuntimeError("PostgreSQL admission authority is required for admission")
        preflight = self.preflight(
            expected_database=expected_database,
            require_empty_catalogue_authority=True,
        )
        admission = self.database.admit(sources)
        read_back = self.database.verify_read_back(sources)
        postflight = self.preflight(
            expected_database=expected_database,
            require_empty_catalogue_authority=False,
        )
        self._assert_b_closure_counts(postflight)
        return sources, preflight, admission, read_back, postflight

    def verify(
        self,
        *,
        expected_database: str = "npp_dev",
    ) -> tuple[
        tuple[QualifiedEnigmaSource, ...],
        PostgreSQLPreflightReport,
        EnigmaReadBackReceipt,
    ]:
        sources = self.qualify_sources()
        if self.database is None:
            raise RuntimeError("PostgreSQL admission authority is required for verification")
        preflight = self.preflight(
            expected_database=expected_database,
            require_empty_catalogue_authority=False,
        )
        self._assert_b_closure_counts(preflight)
        read_back = self.database.verify_read_back(sources)
        return sources, preflight, read_back

    def qualify_adapter(
        self,
        *,
        expected_database: str = "npp_dev",
    ) -> tuple[
        tuple[QualifiedEnigmaSource, ...],
        PostgreSQLPreflightReport,
        EnigmaAdapterQualificationReceipt,
    ]:
        sources = self.qualify_sources()
        if self.database is None:
            raise RuntimeError("PostgreSQL admission authority is required for adapter qualification")
        preflight = self.preflight(
            expected_database=expected_database,
            require_empty_catalogue_authority=False,
        )
        self._assert_b_closure_counts(preflight)
        receipt = self.database.qualify_read_adapter(sources)
        return sources, preflight, receipt


__all__ = ["GovernedEnigmaCatalogueService"]
