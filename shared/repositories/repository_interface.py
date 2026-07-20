"""
============================================================
Nexa Provider Platform
File: shared/repositories/repository_interface.py
Layer: Shared Repository Foundation
Milestone: NPP-M005 — Repository Foundation
============================================================

Defines the storage-independent contract implemented by all
repository implementations.

Provider Services depend on this interface rather than JSON,
JSONL, CSV, Supabase, PostgreSQL, filesystem paths, or storage
adapters. Concrete repositories may change without requiring
changes to provider business logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from .repository_result import RepositoryResult


class RepositoryInterface(ABC):
    """
    Abstract contract for provider-record repositories.

    Implementations are responsible for persistence mechanics,
    record lookup, duplicate protection, immutable identifier
    enforcement, and translation of backend failures into the
    repository exception hierarchy.

    Domain-specific validation, authorization, event creation,
    audit creation, synchronization policy, and transport logic
    remain outside this interface.
    """

    @property
    @abstractmethod
    def repository_name(self) -> str:
        """Return the logical repository name."""

    @property
    @abstractmethod
    def repository_type(self) -> str:
        """Return the concrete repository implementation type."""

    @property
    @abstractmethod
    def id_field(self) -> str:
        """Return the immutable primary identifier field name."""

    @abstractmethod
    def create(
        self,
        record: Mapping[str, Any],
    ) -> RepositoryResult:
        """
        Persist one new record.

        Implementations must reject missing identifiers and
        duplicate records.
        """

    @abstractmethod
    def get(
        self,
        record_id: str,
    ) -> RepositoryResult:
        """
        Retrieve one record by its immutable identifier.

        Implementations must raise a repository not-found error
        when the requested record does not exist.
        """

    @abstractmethod
    def update(
        self,
        record_id: str,
        record: Mapping[str, Any],
    ) -> RepositoryResult:
        """
        Apply a partial update to an existing record.

        Only supplied fields are modified. Fields omitted from the
        update mapping remain unchanged.

        Implementations must reject empty update mappings and
        attempts to alter the immutable primary identifier.
        """

    @abstractmethod
    def delete(
        self,
        record_id: str,
    ) -> RepositoryResult:
        """
        Delete one record where deletion is permitted.

        Provider domains may prohibit deletion and use lifecycle
        statuses instead.
        """

    @abstractmethod
    def list_all(self) -> RepositoryResult:
        """
        Return all records in deterministic order where practical.

        An empty repository must return a successful result with
        an empty record collection.
        """

    @abstractmethod
    def exists(
        self,
        record_id: str,
    ) -> RepositoryResult:
        """Return a successful result describing record existence."""

    @abstractmethod
    def count(self) -> RepositoryResult:
        """Return a successful result containing the record count."""


__all__ = [
    "RepositoryInterface",
]
