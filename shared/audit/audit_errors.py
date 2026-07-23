"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_errors.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.1.1 / M007.4 — Audit Error Contracts
Revision: v2
============================================================

Defines the contract-level exception hierarchy used by the
Shared Audit Infrastructure.

Audit exceptions communicate invalid audit identifiers,
timestamps, metadata and record-contract violations without
coupling the audit layer to repository, storage, event or
provider-specific exception types.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping


AUDIT_ERROR_PREFIX = "NPP-AUDIT"


class AuditError(Exception):
    """
    Base exception for Shared Audit Infrastructure failures.

    Parameters
    ----------
    message:
        Human-readable error description.

    audit_id:
        Identifier of the affected audit record, when known.

    action:
        Stable audit action associated with the failure, when known.

    metadata:
        Additional implementation-neutral diagnostic context.
    """

    error_code = f"{AUDIT_ERROR_PREFIX}-001"

    def __init__(
        self,
        message: str,
        *,
        audit_id: str | None = None,
        action: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        if not isinstance(message, str):
            raise TypeError("message must be a string.")

        normalized_message = message.strip()

        if not normalized_message:
            raise ValueError("message must not be empty.")

        normalized_audit_id = self._normalize_optional_text(
            audit_id,
            field_name="audit_id",
        )
        normalized_action = self._normalize_optional_text(
            action,
            field_name="action",
        )

        if metadata is not None and not isinstance(metadata, Mapping):
            raise TypeError("metadata must be a mapping.")

        super().__init__(normalized_message)

        self._message = normalized_message
        self._audit_id = normalized_audit_id
        self._action = normalized_action
        self._metadata = MappingProxyType(dict(metadata or {}))

    @staticmethod
    def _normalize_optional_text(
        value: str | None,
        *,
        field_name: str,
    ) -> str | None:
        """Validate and normalize an optional non-empty string."""

        if value is None:
            return None

        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty when provided."
            )

        return normalized

    @property
    def message(self) -> str:
        """Return the human-readable error description."""

        return self._message

    @property
    def audit_id(self) -> str | None:
        """Return the affected audit-record identifier, when known."""

        return self._audit_id

    @property
    def action(self) -> str | None:
        """Return the associated audit action, when known."""

        return self._action

    @property
    def metadata(self) -> Mapping[str, Any]:
        """Return immutable implementation-neutral error context."""

        return self._metadata

    def to_dict(self) -> dict[str, Any]:
        """Serialize the audit error into a detached dictionary."""

        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "audit_id": self.audit_id,
            "action": self.action,
            "metadata": dict(self.metadata),
        }


class AuditValidationError(AuditError, ValueError):
    """Raised when an audit record violates its required contract."""

    error_code = f"{AUDIT_ERROR_PREFIX}-010"


class AuditIdentifierError(AuditValidationError):
    """Raised when an audit-record identifier is invalid."""

    error_code = f"{AUDIT_ERROR_PREFIX}-011"


class AuditTimestampError(AuditValidationError):
    """Raised when an audit timestamp is invalid or timezone-naive."""

    error_code = f"{AUDIT_ERROR_PREFIX}-012"


class AuditMetadataError(AuditValidationError):
    """Raised when audit metadata violates its required contract."""

    error_code = f"{AUDIT_ERROR_PREFIX}-013"


class AuditRepositoryError(AuditError, RuntimeError):
    """Base exception for audit repository failures."""

    error_code = f"{AUDIT_ERROR_PREFIX}-100"


class AuditRepositoryConfigurationError(AuditRepositoryError, ValueError):
    """Raised when repository configuration is invalid."""

    error_code = f"{AUDIT_ERROR_PREFIX}-101"


class AuditRepositoryOperationError(AuditRepositoryError):
    """Base exception for failed repository operations."""

    error_code = f"{AUDIT_ERROR_PREFIX}-110"


class AuditAppendError(AuditRepositoryOperationError):
    error_code = f"{AUDIT_ERROR_PREFIX}-111"


class AuditReadError(AuditRepositoryOperationError):
    error_code = f"{AUDIT_ERROR_PREFIX}-112"


class AuditListError(AuditRepositoryOperationError):
    error_code = f"{AUDIT_ERROR_PREFIX}-113"


class AuditExistsError(AuditRepositoryOperationError):
    error_code = f"{AUDIT_ERROR_PREFIX}-114"


class AuditCountError(AuditRepositoryOperationError):
    error_code = f"{AUDIT_ERROR_PREFIX}-115"


class AuditRecordRepositoryError(AuditRepositoryError):
    """Base exception for repository record failures."""

    error_code = f"{AUDIT_ERROR_PREFIX}-120"


class AuditRecordNotFoundError(AuditRecordRepositoryError, LookupError):
    error_code = f"{AUDIT_ERROR_PREFIX}-121"


class AuditDuplicateRecordError(AuditRecordRepositoryError, ValueError):
    error_code = f"{AUDIT_ERROR_PREFIX}-122"


class AuditInvalidRecordError(AuditRecordRepositoryError, ValueError):
    error_code = f"{AUDIT_ERROR_PREFIX}-123"


__all__ = [
    "AUDIT_ERROR_PREFIX",
    "AuditError",
    "AuditIdentifierError",
    "AuditMetadataError",
    "AuditTimestampError",
    "AuditValidationError",
    "AuditRepositoryError",
    "AuditRepositoryConfigurationError",
    "AuditRepositoryOperationError",
    "AuditAppendError",
    "AuditReadError",
    "AuditListError",
    "AuditExistsError",
    "AuditCountError",
    "AuditRecordRepositoryError",
    "AuditRecordNotFoundError",
    "AuditDuplicateRecordError",
    "AuditInvalidRecordError",
]
