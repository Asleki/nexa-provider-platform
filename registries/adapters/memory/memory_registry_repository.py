"""
============================================================
Nexa Provider Platform
File: registries/adapters/memory/memory_registry_repository.py
Layer: Master Registry Foundation
Milestone: NPP-M008.5 — Memory Registry Repository
============================================================

Thread-safe, deterministic, process-local implementation of the
M008.4 registry repository interface.

This adapter is for tests, simulations, local development, and later
factory integration. It is not durable storage and does not publish
events, write audit records, issue identifiers, enforce lifecycle
policy, or call external systems.
============================================================
"""

from __future__ import annotations

from threading import RLock

from registries.core.base_registry import BaseRegistry
from registries.ports.base_registry_repository import BaseRegistryRepository
from registries.ports.registry_repository_errors import (
    RegistryAddError,
    RegistryClearError,
    RegistryCountError,
    RegistryDuplicateError,
    RegistryExistsError,
    RegistryListError,
    RegistryNotFoundError,
    RegistryReadError,
    RegistryRemoveError,
    RegistryReplaceError,
    RegistryRepositoryError,
)
from registries.ports.registry_repository_result import RegistryRepositoryResult
from registries.ports.registry_repository_types import RegistryRepositoryOperation


class MemoryRegistryRepository(BaseRegistryRepository):
    """In-process repository for immutable ``BaseRegistry`` objects."""

    def __init__(
        self,
        repository_name: str = "memory_registry_repository",
    ) -> None:
        super().__init__(
            repository_name=repository_name,
            repository_type="memory",
        )
        self._registries: dict[str, BaseRegistry] = {}
        self._lock = RLock()

    def _result_metadata(self) -> dict[str, str]:
        return {"repository_type": self.repository_type}

    def add(self, registry: BaseRegistry) -> RegistryRepositoryResult:
        operation = RegistryRepositoryOperation.ADD
        try:
            validated = self.validate_registry(registry)
            registry_id = validated.registry_id
            with self._lock:
                if registry_id in self._registries:
                    raise RegistryDuplicateError(
                        "BaseRegistry with this registry_id already exists.",
                        operation=operation,
                        repository=self.repository_name,
                        registry_id=registry_id,
                        repository_type=self.repository_type,
                    )
                self._registries[registry_id] = validated
            return RegistryRepositoryResult.added(
                repository=self.repository_name,
                registry=validated,
                metadata=self._result_metadata(),
            )
        except RegistryRepositoryError:
            raise
        except Exception as exc:
            raise RegistryAddError(
                "BaseRegistry could not be added.",
                operation=operation,
                repository=self.repository_name,
                registry_id=(
                    registry.registry_id
                    if isinstance(registry, BaseRegistry)
                    else None
                ),
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def get(self, registry_id: str) -> RegistryRepositoryResult:
        operation = RegistryRepositoryOperation.READ
        normalized_id = self.validate_registry_id(registry_id)
        try:
            with self._lock:
                registry = self._registries.get(normalized_id)
            if registry is None:
                raise RegistryNotFoundError(
                    "BaseRegistry was not found.",
                    operation=operation,
                    repository=self.repository_name,
                    registry_id=normalized_id,
                    repository_type=self.repository_type,
                )
            return RegistryRepositoryResult.found(
                repository=self.repository_name,
                registry=registry,
                metadata=self._result_metadata(),
            )
        except RegistryRepositoryError:
            raise
        except Exception as exc:
            raise RegistryReadError(
                "BaseRegistry could not be read.",
                operation=operation,
                repository=self.repository_name,
                registry_id=normalized_id,
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def replace(self, registry: BaseRegistry) -> RegistryRepositoryResult:
        operation = RegistryRepositoryOperation.REPLACE
        try:
            validated = self.validate_registry(registry)
            registry_id = validated.registry_id
            with self._lock:
                if registry_id not in self._registries:
                    raise RegistryNotFoundError(
                        "BaseRegistry was not found.",
                        operation=operation,
                        repository=self.repository_name,
                        registry_id=registry_id,
                        repository_type=self.repository_type,
                    )
                self._registries[registry_id] = validated
            return RegistryRepositoryResult.replaced(
                repository=self.repository_name,
                registry=validated,
                metadata=self._result_metadata(),
            )
        except RegistryRepositoryError:
            raise
        except Exception as exc:
            raise RegistryReplaceError(
                "BaseRegistry could not be replaced.",
                operation=operation,
                repository=self.repository_name,
                registry_id=(
                    registry.registry_id
                    if isinstance(registry, BaseRegistry)
                    else None
                ),
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def remove(self, registry_id: str) -> RegistryRepositoryResult:
        operation = RegistryRepositoryOperation.REMOVE
        normalized_id = self.validate_registry_id(registry_id)
        try:
            with self._lock:
                if normalized_id not in self._registries:
                    raise RegistryNotFoundError(
                        "BaseRegistry was not found.",
                        operation=operation,
                        repository=self.repository_name,
                        registry_id=normalized_id,
                        repository_type=self.repository_type,
                    )
                del self._registries[normalized_id]
            return RegistryRepositoryResult.removed(
                repository=self.repository_name,
                registry_id=normalized_id,
                metadata=self._result_metadata(),
            )
        except RegistryRepositoryError:
            raise
        except Exception as exc:
            raise RegistryRemoveError(
                "BaseRegistry could not be removed.",
                operation=operation,
                repository=self.repository_name,
                registry_id=normalized_id,
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def list_all(self) -> RegistryRepositoryResult:
        operation = RegistryRepositoryOperation.LIST
        try:
            with self._lock:
                registries = tuple(self._registries.values())
            return RegistryRepositoryResult.listed(
                repository=self.repository_name,
                registries=registries,
                metadata=self._result_metadata(),
            )
        except RegistryRepositoryError:
            raise
        except Exception as exc:
            raise RegistryListError(
                "BaseRegistry records could not be listed.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def exists(self, registry_id: str) -> RegistryRepositoryResult:
        operation = RegistryRepositoryOperation.EXISTS
        normalized_id = self.validate_registry_id(registry_id)
        try:
            with self._lock:
                found = normalized_id in self._registries
            return RegistryRepositoryResult.existence_checked(
                repository=self.repository_name,
                registry_id=normalized_id,
                exists=found,
                metadata=self._result_metadata(),
            )
        except RegistryRepositoryError:
            raise
        except Exception as exc:
            raise RegistryExistsError(
                "BaseRegistry existence could not be checked.",
                operation=operation,
                repository=self.repository_name,
                registry_id=normalized_id,
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def count(self) -> RegistryRepositoryResult:
        operation = RegistryRepositoryOperation.COUNT
        try:
            with self._lock:
                registry_count = len(self._registries)
            return RegistryRepositoryResult.counted(
                repository=self.repository_name,
                count=registry_count,
                metadata=self._result_metadata(),
            )
        except RegistryRepositoryError:
            raise
        except Exception as exc:
            raise RegistryCountError(
                "BaseRegistry records could not be counted.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                cause=exc,
            ) from exc

    def clear(self) -> RegistryRepositoryResult:
        operation = RegistryRepositoryOperation.CLEAR
        try:
            with self._lock:
                records_affected = len(self._registries)
                self._registries.clear()
            return RegistryRepositoryResult.cleared(
                repository=self.repository_name,
                records_affected=records_affected,
                metadata=self._result_metadata(),
            )
        except RegistryRepositoryError:
            raise
        except Exception as exc:
            raise RegistryClearError(
                "Memory registry repository could not be cleared.",
                operation=operation,
                repository=self.repository_name,
                repository_type=self.repository_type,
                cause=exc,
            ) from exc


__all__ = ["MemoryRegistryRepository"]
