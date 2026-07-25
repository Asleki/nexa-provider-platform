"""
============================================================
Nexa Provider Platform
File: registries/ports/registry_repository_result.py
Layer: Master Registry Foundation
Milestone: NPP-M008.4 — Registry Repository Interface
============================================================

Immutable result contract for successful registry repository operations.
Failures are represented by the registry repository error hierarchy.
============================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from registries.core.base_registry import BaseRegistry

from .registry_repository_types import RegistryRepositoryOperation


@dataclass(frozen=True, slots=True)
class RegistryRepositoryResult:
    """Result returned by successful registry repository operations."""

    success: bool
    operation: RegistryRepositoryOperation
    repository: str
    registry_id: str | None = None
    registry: BaseRegistry | None = None
    registries: tuple[BaseRegistry, ...] = ()
    records_affected: int = 0
    message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean.")

        operation = self.operation
        if not isinstance(operation, RegistryRepositoryOperation):
            try:
                operation = RegistryRepositoryOperation(str(operation))
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "operation must be a supported registry repository operation."
                ) from exc
            object.__setattr__(self, "operation", operation)

        if not isinstance(self.repository, str):
            raise TypeError("repository must be text.")
        repository = self.repository.strip()
        if not repository:
            raise ValueError("repository must not be empty.")
        object.__setattr__(self, "repository", repository)

        if self.registry_id is not None:
            if not isinstance(self.registry_id, str):
                raise TypeError("registry_id must be text when provided.")
            registry_id = self.registry_id.strip()
            if not registry_id:
                raise ValueError(
                    "registry_id must not be empty when provided."
                )
            object.__setattr__(self, "registry_id", registry_id)

        if self.registry is not None and not isinstance(
            self.registry,
            BaseRegistry,
        ):
            raise TypeError("registry must be a BaseRegistry when provided.")

        normalized_registries = tuple(self.registries)
        if any(
            not isinstance(registry, BaseRegistry)
            for registry in normalized_registries
        ):
            raise TypeError(
                "registries must contain only BaseRegistry instances."
            )
        object.__setattr__(self, "registries", normalized_registries)

        if (
            not isinstance(self.records_affected, int)
            or isinstance(self.records_affected, bool)
        ):
            raise TypeError("records_affected must be an integer.")
        if self.records_affected < 0:
            raise ValueError("records_affected must not be negative.")

        if not isinstance(self.message, str):
            raise TypeError("message must be text.")
        object.__setattr__(self, "message", self.message.strip())

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )

    @property
    def failed(self) -> bool:
        return not self.success

    @property
    def count(self) -> int:
        if self.operation is RegistryRepositoryOperation.LIST:
            return len(self.registries)
        return self.records_affected

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "operation": self.operation.value,
            "repository": self.repository,
            "registry_id": self.registry_id,
            "registry": (
                self.registry.to_dict()
                if self.registry is not None
                else None
            ),
            "registries": [
                registry.to_dict()
                for registry in self.registries
            ],
            "records_affected": self.records_affected,
            "message": self.message,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def added(
        cls,
        *,
        repository: str,
        registry: BaseRegistry,
        metadata: Mapping[str, Any] | None = None,
    ) -> "RegistryRepositoryResult":
        return cls(
            success=True,
            operation=RegistryRepositoryOperation.ADD,
            repository=repository,
            registry_id=registry.registry_id,
            registry=registry,
            records_affected=1,
            message="Registry added.",
            metadata=metadata or {},
        )

    @classmethod
    def found(
        cls,
        *,
        repository: str,
        registry: BaseRegistry,
        metadata: Mapping[str, Any] | None = None,
    ) -> "RegistryRepositoryResult":
        return cls(
            success=True,
            operation=RegistryRepositoryOperation.READ,
            repository=repository,
            registry_id=registry.registry_id,
            registry=registry,
            records_affected=1,
            message="Registry found.",
            metadata=metadata or {},
        )

    @classmethod
    def replaced(
        cls,
        *,
        repository: str,
        registry: BaseRegistry,
        metadata: Mapping[str, Any] | None = None,
    ) -> "RegistryRepositoryResult":
        return cls(
            success=True,
            operation=RegistryRepositoryOperation.REPLACE,
            repository=repository,
            registry_id=registry.registry_id,
            registry=registry,
            records_affected=1,
            message="Registry replaced.",
            metadata=metadata or {},
        )

    @classmethod
    def removed(
        cls,
        *,
        repository: str,
        registry_id: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "RegistryRepositoryResult":
        return cls(
            success=True,
            operation=RegistryRepositoryOperation.REMOVE,
            repository=repository,
            registry_id=registry_id,
            records_affected=1,
            message="Registry removed.",
            metadata=metadata or {},
        )

    @classmethod
    def listed(
        cls,
        *,
        repository: str,
        registries: tuple[BaseRegistry, ...],
        metadata: Mapping[str, Any] | None = None,
    ) -> "RegistryRepositoryResult":
        normalized = tuple(registries)
        return cls(
            success=True,
            operation=RegistryRepositoryOperation.LIST,
            repository=repository,
            registries=normalized,
            records_affected=len(normalized),
            message="Registries listed.",
            metadata=metadata or {},
        )

    @classmethod
    def existence_checked(
        cls,
        *,
        repository: str,
        registry_id: str,
        exists: bool,
        metadata: Mapping[str, Any] | None = None,
    ) -> "RegistryRepositoryResult":
        combined_metadata = dict(metadata or {})
        combined_metadata["exists"] = bool(exists)
        return cls(
            success=True,
            operation=RegistryRepositoryOperation.EXISTS,
            repository=repository,
            registry_id=registry_id,
            records_affected=1 if exists else 0,
            message=(
                "Registry exists."
                if exists
                else "Registry does not exist."
            ),
            metadata=combined_metadata,
        )

    @classmethod
    def counted(
        cls,
        *,
        repository: str,
        count: int,
        metadata: Mapping[str, Any] | None = None,
    ) -> "RegistryRepositoryResult":
        if (
            not isinstance(count, int)
            or isinstance(count, bool)
            or count < 0
        ):
            raise ValueError("count must be a non-negative integer.")
        combined_metadata = dict(metadata or {})
        combined_metadata["count"] = count
        return cls(
            success=True,
            operation=RegistryRepositoryOperation.COUNT,
            repository=repository,
            records_affected=count,
            message="Registries counted.",
            metadata=combined_metadata,
        )

    @classmethod
    def cleared(
        cls,
        *,
        repository: str,
        records_affected: int,
        metadata: Mapping[str, Any] | None = None,
    ) -> "RegistryRepositoryResult":
        return cls(
            success=True,
            operation=RegistryRepositoryOperation.CLEAR,
            repository=repository,
            records_affected=records_affected,
            message="Registry repository cleared.",
            metadata=metadata or {},
        )


__all__ = ["RegistryRepositoryResult"]
