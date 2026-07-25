"""
============================================================
Nexa Provider Platform
File: registries/ports/registry_repository.py
Layer: Master Registry Foundation
Milestone: NPP-M008.4 — Registry Repository Interface
============================================================

Storage-independent contract implemented by every registry repository.

The interface stores complete BaseRegistry objects. It does not perform
partial field patches, lifecycle authorization, validation policy,
identifier issuance, event publication, audit creation, synchronization,
transport, or concrete persistence.
============================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from registries.core.base_registry import BaseRegistry

from .registry_repository_result import RegistryRepositoryResult


class RegistryRepositoryInterface(ABC):
    """Abstract contract for registry-definition repositories."""

    @property
    @abstractmethod
    def repository_name(self) -> str:
        """Return the logical repository name."""

    @property
    @abstractmethod
    def repository_type(self) -> str:
        """Return the concrete implementation type."""

    @abstractmethod
    def add(
        self,
        registry: BaseRegistry,
    ) -> RegistryRepositoryResult:
        """Persist one new registry and reject duplicate registry IDs."""

    @abstractmethod
    def get(
        self,
        registry_id: str,
    ) -> RegistryRepositoryResult:
        """Retrieve one registry by its immutable registry ID."""

    @abstractmethod
    def replace(
        self,
        registry: BaseRegistry,
    ) -> RegistryRepositoryResult:
        """Atomically replace one complete existing registry object."""

    @abstractmethod
    def remove(
        self,
        registry_id: str,
    ) -> RegistryRepositoryResult:
        """Remove one registry where the implementation permits it."""

    @abstractmethod
    def list_all(self) -> RegistryRepositoryResult:
        """Return all registries in deterministic order where practical."""

    @abstractmethod
    def exists(
        self,
        registry_id: str,
    ) -> RegistryRepositoryResult:
        """Return whether a registry ID exists."""

    @abstractmethod
    def count(self) -> RegistryRepositoryResult:
        """Return the number of stored registries."""

    @abstractmethod
    def clear(self) -> RegistryRepositoryResult:
        """Clear all registries where the implementation permits it."""


__all__ = ["RegistryRepositoryInterface"]
