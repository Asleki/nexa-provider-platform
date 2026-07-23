"""
Nexa Provider Platform
File: shared/audit/audit_integrity_result.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.6 — Audit Integrity Validation
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .audit_errors import AuditIntegrityResultError


class AuditIntegrityStatus(str, Enum):
    """Supported outcomes for deterministic audit integrity validation."""

    VALID = "VALID"
    INVALID = "INVALID"


@dataclass(frozen=True, slots=True)
class AuditIntegrityFinding:
    """One immutable reason produced by integrity validation."""

    code: str
    message: str
    audit_id: str | None = None
    record_index: int | None = None

    def __post_init__(self) -> None:
        for name in ("code", "message"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise AuditIntegrityResultError(f"{name} must be a string.")
            normalized = value.strip()
            if not normalized:
                raise AuditIntegrityResultError(f"{name} must not be empty.")
            object.__setattr__(self, name, normalized)

        if self.audit_id is not None:
            if not isinstance(self.audit_id, str):
                raise AuditIntegrityResultError("audit_id must be a string.")
            normalized = self.audit_id.strip()
            if not normalized:
                raise AuditIntegrityResultError(
                    "audit_id must not be empty when provided."
                )
            object.__setattr__(self, "audit_id", normalized)

        if self.record_index is not None:
            if isinstance(self.record_index, bool) or not isinstance(
                self.record_index, int
            ):
                raise AuditIntegrityResultError(
                    "record_index must be an integer."
                )
            if self.record_index < 0:
                raise AuditIntegrityResultError(
                    "record_index must not be negative."
                )


@dataclass(frozen=True, slots=True)
class AuditIntegrityResult:
    """Immutable validation result for one audit-record sequence."""

    status: AuditIntegrityStatus
    records_checked: int
    findings: tuple[AuditIntegrityFinding, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, AuditIntegrityStatus):
            raise AuditIntegrityResultError(
                "status must be an AuditIntegrityStatus value."
            )
        if isinstance(self.records_checked, bool) or not isinstance(
            self.records_checked, int
        ):
            raise AuditIntegrityResultError(
                "records_checked must be an integer."
            )
        if self.records_checked < 0:
            raise AuditIntegrityResultError(
                "records_checked must not be negative."
            )
        if not isinstance(self.findings, tuple):
            raise AuditIntegrityResultError("findings must be a tuple.")
        if any(
            not isinstance(finding, AuditIntegrityFinding)
            for finding in self.findings
        ):
            raise AuditIntegrityResultError(
                "findings must contain only AuditIntegrityFinding values."
            )
        expected = (
            AuditIntegrityStatus.INVALID
            if self.findings
            else AuditIntegrityStatus.VALID
        )
        if self.status is not expected:
            raise AuditIntegrityResultError(
                "status is inconsistent with findings."
            )

    @property
    def is_valid(self) -> bool:
        return self.status is AuditIntegrityStatus.VALID

    @property
    def is_invalid(self) -> bool:
        return not self.is_valid


__all__ = [
    "AuditIntegrityFinding",
    "AuditIntegrityResult",
    "AuditIntegrityStatus",
]
