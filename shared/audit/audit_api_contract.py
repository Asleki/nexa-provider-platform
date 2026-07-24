"""
Nexa Provider Platform
File: shared/audit/audit_api_contract.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.8 — Audit API Contracts
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .audit_api_operation import AuditApiOperation
from .audit_errors import AuditApiContractError


@dataclass(frozen=True, slots=True)
class AuditApiContract:
    """Versioned declaration of supported audit API operations."""

    name: str = "audit"
    version: int = 1
    operations: tuple[AuditApiOperation, ...] = tuple(AuditApiOperation)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise AuditApiContractError("name must be a non-empty string.")
        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise AuditApiContractError("version must be an integer.")
        if self.version < 1:
            raise AuditApiContractError("version must be greater than zero.")
        if not isinstance(self.operations, tuple):
            raise AuditApiContractError("operations must be a tuple.")
        parsed = tuple(AuditApiOperation.parse(item) for item in self.operations)
        if not parsed:
            raise AuditApiContractError(
                "operations must contain at least one operation."
            )
        if len(parsed) != len(set(parsed)):
            raise AuditApiContractError("operations must be unique.")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "operations", parsed)

    @property
    def identifier(self) -> str:
        return f"{self.name}.v{self.version}"

    def supports(self, operation: AuditApiOperation | str) -> bool:
        try:
            parsed = AuditApiOperation.parse(operation)
        except Exception:
            return False
        return parsed in self.operations

    def to_dict(self) -> Mapping[str, object]:
        return MappingProxyType(
            {
                "name": self.name,
                "version": self.version,
                "identifier": self.identifier,
                "operations": tuple(item.value for item in self.operations),
            }
        )


__all__ = ["AuditApiContract"]
