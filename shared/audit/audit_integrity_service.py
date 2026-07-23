"""
Nexa Provider Platform
File: shared/audit/audit_integrity_service.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.6 — Audit Integrity Validation
"""
from __future__ import annotations

from collections.abc import Sequence

from .audit_errors import (
    AuditIntegrityExecutionError,
    AuditIntegrityServiceConfigurationError,
    AuditIntegrityValidationError,
)
from .audit_integrity_result import AuditIntegrityResult
from .audit_integrity_service_interface import AuditIntegrityServiceInterface
from .audit_integrity_validator import AuditIntegrityValidator
from .audit_record import AuditRecord


class AuditIntegrityService(AuditIntegrityServiceInterface):
    """Read-only application service delegating deterministic validation."""

    def __init__(
        self,
        validator: AuditIntegrityValidator | None = None,
    ) -> None:
        if validator is not None and not isinstance(
            validator, AuditIntegrityValidator
        ):
            raise AuditIntegrityServiceConfigurationError(
                "validator must be an AuditIntegrityValidator."
            )
        self._validator = validator or AuditIntegrityValidator()

    @property
    def validator(self) -> AuditIntegrityValidator:
        return self._validator

    def validate_record(self, record: AuditRecord) -> AuditIntegrityResult:
        try:
            return self._validator.validate_record(record)
        except AuditIntegrityValidationError:
            raise
        except Exception as exc:
            raise AuditIntegrityExecutionError(
                "Audit integrity validation failed."
            ) from exc

    def validate_records(
        self,
        records: Sequence[AuditRecord],
    ) -> AuditIntegrityResult:
        try:
            return self._validator.validate_records(records)
        except AuditIntegrityValidationError:
            raise
        except Exception as exc:
            raise AuditIntegrityExecutionError(
                "Audit integrity validation failed."
            ) from exc


__all__ = ["AuditIntegrityService"]
