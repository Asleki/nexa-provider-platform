"""Immutable result returned by registry audit integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from shared.audit import AuditRepositoryResult

from .registry_audit_errors import RegistryAuditResultError


@dataclass(frozen=True, slots=True)
class RegistryAuditResult:
    """Stable success or failure envelope for one registry audit attempt."""

    attempted: bool
    success: bool
    audit_id: str | None = None
    event_id: str | None = None
    event_type: str | None = None
    repository_result: AuditRepositoryResult | None = None
    error_code: str | None = None
    error_type: str | None = None
    message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.attempted, bool) or not isinstance(self.success, bool):
            raise RegistryAuditResultError("attempted and success must be bool values.")
        if not isinstance(self.message, str):
            raise RegistryAuditResultError("message must be a string.")
        if not isinstance(self.metadata, Mapping):
            raise RegistryAuditResultError("metadata must be a mapping.")

        audit_id = self._optional_text("audit_id", self.audit_id)
        event_id = self._optional_text("event_id", self.event_id)
        event_type = self._optional_text("event_type", self.event_type)
        error_code = self._optional_text("error_code", self.error_code)
        error_type = self._optional_text("error_type", self.error_type)
        message = self.message.strip()

        if (event_id is None) != (event_type is None):
            raise RegistryAuditResultError("event_id and event_type must be provided together.")
        if self.repository_result is not None and not isinstance(
            self.repository_result, AuditRepositoryResult
        ):
            raise RegistryAuditResultError(
                "repository_result must be AuditRepositoryResult."
            )

        if not self.attempted:
            if self.success:
                raise RegistryAuditResultError(
                    "successful audit results must be attempted."
                )
            if any(
                value is not None
                for value in (
                    audit_id,
                    event_id,
                    event_type,
                    self.repository_result,
                    error_code,
                    error_type,
                )
            ) or message:
                raise RegistryAuditResultError(
                    "unattempted audit results must not contain execution details."
                )
        elif self.success:
            if self.repository_result is None:
                raise RegistryAuditResultError(
                    "successful audit results require repository_result."
                )
            if not self.repository_result.success:
                raise RegistryAuditResultError(
                    "successful audit results require a successful repository_result."
                )
            if audit_id is None:
                raise RegistryAuditResultError(
                    "successful audit results require audit_id."
                )
            if self.repository_result.audit_id != audit_id:
                raise RegistryAuditResultError(
                    "audit_id must match repository_result.audit_id."
                )
            if error_code is not None or error_type is not None:
                raise RegistryAuditResultError(
                    "successful audit results must not contain failure details."
                )
            if not message:
                raise RegistryAuditResultError(
                    "successful audit results require a message."
                )
        else:
            if audit_id is not None or self.repository_result is not None:
                raise RegistryAuditResultError(
                    "failed audit results must not contain repository success data."
                )
            if error_code is None or error_type is None:
                raise RegistryAuditResultError(
                    "failed audit results require error_code and error_type."
                )
            if not message:
                raise RegistryAuditResultError(
                    "failed audit results require a message."
                )

        object.__setattr__(self, "audit_id", audit_id)
        object.__setattr__(self, "event_id", event_id)
        object.__setattr__(self, "event_type", event_type)
        object.__setattr__(self, "error_code", error_code)
        object.__setattr__(self, "error_type", error_type)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @staticmethod
    def _optional_text(name: str, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise RegistryAuditResultError(f"{name} must be a string when provided.")
        normalized = value.strip()
        if not normalized:
            raise RegistryAuditResultError(f"{name} must not be empty when provided.")
        return normalized

    @classmethod
    def recorded(
        cls,
        repository_result: AuditRepositoryResult,
        *,
        event_id: str | None = None,
        event_type: str | None = None,
    ) -> "RegistryAuditResult":
        if not isinstance(repository_result, AuditRepositoryResult):
            raise RegistryAuditResultError(
                "repository_result must be AuditRepositoryResult."
            )
        return cls(
            attempted=True,
            success=True,
            audit_id=repository_result.audit_id,
            event_id=event_id,
            event_type=event_type,
            repository_result=repository_result,
            message="Registry audit recorded.",
        )

    @classmethod
    def failed(
        cls,
        *,
        error_code: str,
        error_type: str,
        message: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "RegistryAuditResult":
        return cls(
            attempted=True,
            success=False,
            error_code=error_code,
            error_type=error_type,
            message=message,
            metadata=metadata or {},
        )

    def to_metadata(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "audit_attempted": self.attempted,
            "audit_success": self.success,
        }
        if self.audit_id:
            value["audit_id"] = self.audit_id
        if self.event_id:
            value.update(
                {
                    "audit_event_id": self.event_id,
                    "audit_event_type": self.event_type,
                }
            )
        if self.error_code:
            value.update(
                {
                    "audit_error_code": self.error_code,
                    "audit_error_type": self.error_type,
                    "audit_requires_attention": True,
                }
            )
        return value


__all__ = ["RegistryAuditResult"]
