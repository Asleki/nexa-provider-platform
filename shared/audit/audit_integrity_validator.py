"""
Nexa Provider Platform
File: shared/audit/audit_integrity_validator.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.6 — Audit Integrity Validation
"""
from __future__ import annotations

from collections.abc import Sequence

from .audit_errors import AuditIntegrityValidationError
from .audit_integrity_result import (
    AuditIntegrityFinding,
    AuditIntegrityResult,
    AuditIntegrityStatus,
)
from .audit_record import AuditRecord


class AuditIntegrityValidator:
    """
    Deterministic, read-only validator for canonical AuditRecord sequences.

    This milestone performs structural and sequence validation only. It does
    not claim cryptographic proof because AuditRecord currently exposes no
    hash-chain or signature contract.
    """

    def validate_record(self, record: AuditRecord) -> AuditIntegrityResult:
        if not isinstance(record, AuditRecord):
            raise AuditIntegrityValidationError(
                "record must be an AuditRecord."
            )
        return self.validate_records((record,))

    def validate_records(
        self,
        records: Sequence[AuditRecord],
    ) -> AuditIntegrityResult:
        if isinstance(records, (str, bytes)) or not isinstance(
            records, Sequence
        ):
            raise AuditIntegrityValidationError(
                "records must be a sequence of AuditRecord values."
            )

        materialized = tuple(records)
        if any(not isinstance(record, AuditRecord) for record in materialized):
            raise AuditIntegrityValidationError(
                "records must contain only AuditRecord values."
            )

        findings: list[AuditIntegrityFinding] = []
        seen_ids: dict[str, int] = {}

        for index, record in enumerate(materialized):
            first_index = seen_ids.get(record.audit_id)
            if first_index is not None:
                findings.append(
                    AuditIntegrityFinding(
                        code="DUPLICATE_AUDIT_ID",
                        message=(
                            "audit_id duplicates an earlier record at "
                            f"index {first_index}."
                        ),
                        audit_id=record.audit_id,
                        record_index=index,
                    )
                )
            else:
                seen_ids[record.audit_id] = index

            if index > 0:
                previous = materialized[index - 1]
                if record.recorded_at < previous.recorded_at:
                    findings.append(
                        AuditIntegrityFinding(
                            code="NON_CHRONOLOGICAL_ORDER",
                            message=(
                                "recorded_at is earlier than the preceding "
                                "record."
                            ),
                            audit_id=record.audit_id,
                            record_index=index,
                        )
                    )

        status = (
            AuditIntegrityStatus.INVALID
            if findings
            else AuditIntegrityStatus.VALID
        )
        return AuditIntegrityResult(
            status=status,
            records_checked=len(materialized),
            findings=tuple(findings),
        )


__all__ = ["AuditIntegrityValidator"]
