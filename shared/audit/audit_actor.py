"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_actor.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.3.1 — Audit Actor Metadata
============================================================

Defines immutable provider-neutral metadata identifying the actor
responsible for an audited operation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from .audit_errors import AuditMetadataError, AuditValidationError


def _normalize_required_text(name: str, value: str) -> str:
    if not isinstance(value, str):
        raise AuditValidationError(f"{name} must be a string.")

    normalized = value.strip()
    if not normalized:
        raise AuditValidationError(f"{name} must not be empty.")

    return normalized


def _normalize_optional_text(name: str, value: str | None) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise AuditValidationError(f"{name} must be a string.")

    normalized = value.strip()
    if not normalized:
        raise AuditValidationError(
            f"{name} must not be empty when provided."
        )

    return normalized


@dataclass(frozen=True, slots=True)
class AuditActor:
    """Immutable identity and classification of an audit actor."""

    actor_id: str
    actor_type: str
    actor_role: str | None = None
    actor_namespace: str | None = None
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "actor_id",
            _normalize_required_text("actor_id", self.actor_id),
        )
        object.__setattr__(
            self,
            "actor_type",
            _normalize_required_text("actor_type", self.actor_type),
        )
        object.__setattr__(
            self,
            "actor_role",
            _normalize_optional_text("actor_role", self.actor_role),
        )
        object.__setattr__(
            self,
            "actor_namespace",
            _normalize_optional_text(
                "actor_namespace",
                self.actor_namespace,
            ),
        )

        if not isinstance(self.attributes, Mapping):
            raise AuditMetadataError("attributes must be a mapping.")

        object.__setattr__(
            self,
            "attributes",
            MappingProxyType(dict(self.attributes)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize actor metadata to a detached plain dictionary."""

        return {
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "actor_role": self.actor_role,
            "actor_namespace": self.actor_namespace,
            "attributes": dict(self.attributes),
        }


__all__ = ["AuditActor"]
