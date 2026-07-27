"""
============================================================
Nexa Provider Platform
File: registries/governance/lifecycle_result.py
Layer: Master Registry Foundation
Milestone: NPP-M008.8 — Registry Lifecycle
============================================================

Immutable result returned by successful Registry Lifecycle operations.
A result represents either a real immutable transition or an idempotent
no-op. It does not persist the registry, publish events, or write audits.
============================================================
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from registries.core import BaseRegistry, RegistryStatus


@dataclass(frozen=True, slots=True)
class RegistryLifecycleResult:
    """Successful registry-definition lifecycle evaluation result."""

    registry: BaseRegistry
    previous_status: RegistryStatus
    current_status: RegistryStatus
    changed: bool
    message: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.registry, BaseRegistry):
            raise TypeError("registry must be a BaseRegistry instance.")
        if not isinstance(self.previous_status, RegistryStatus):
            raise TypeError("previous_status must be a RegistryStatus.")
        if not isinstance(self.current_status, RegistryStatus):
            raise TypeError("current_status must be a RegistryStatus.")
        if not isinstance(self.changed, bool):
            raise TypeError("changed must be a boolean.")
        if not isinstance(self.message, str):
            raise TypeError("message must be text.")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        if self.registry.status is not self.current_status:
            raise ValueError(
                "registry.status must match current_status."
            )
        if self.changed and self.previous_status is self.current_status:
            raise ValueError(
                "changed cannot be true when statuses are equal."
            )
        if not self.changed and self.previous_status is not self.current_status:
            raise ValueError(
                "changed cannot be false when statuses differ."
            )
        object.__setattr__(self, "message", self.message.strip())
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    @property
    def registry_id(self) -> str:
        """Return the transitioned registry identifier."""

        return self.registry.registry_id

    @property
    def status(self) -> RegistryStatus:
        """Return the resulting registry status."""

        return self.current_status

    @property
    def noop(self) -> bool:
        """Return whether the operation was an idempotent no-op."""

        return not self.changed

    def to_dict(self) -> dict[str, object]:
        """Return a deterministic transport-neutral mapping."""

        return {
            "registry_id": self.registry_id,
            "previous_status": self.previous_status.value,
            "current_status": self.current_status.value,
            "changed": self.changed,
            "message": self.message,
            "metadata": dict(self.metadata),
            "registry": self.registry.to_dict(),
        }


__all__ = ["RegistryLifecycleResult"]
