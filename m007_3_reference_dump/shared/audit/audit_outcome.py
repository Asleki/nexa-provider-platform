"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_outcome.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.1.2 — Audit Outcome Contract
============================================================

Defines the stable outcome vocabulary used by audit records.

AuditOutcome represents the final observed result of an audited
operation. It is intentionally smaller than an event lifecycle:
audit records describe whether an operation succeeded, failed,
or was rejected rather than every processing stage it passed
through.
"""

from __future__ import annotations

from enum import Enum


class AuditOutcome(str, Enum):
    """Final outcomes supported by the Shared Audit Infrastructure."""

    SUCCESS = "success"
    FAILURE = "failure"
    REJECTED = "rejected"

    def __str__(self) -> str:
        """Return the serialized enum value."""

        return self.value

    @property
    def is_success(self) -> bool:
        """Return whether the audited operation completed successfully."""

        return self is AuditOutcome.SUCCESS

    @property
    def is_failure(self) -> bool:
        """Return whether the audited operation did not succeed."""

        return self in {
            AuditOutcome.FAILURE,
            AuditOutcome.REJECTED,
        }


__all__ = [
    "AuditOutcome",
]
