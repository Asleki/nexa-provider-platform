"""
============================================================
Nexa Provider Platform
File: shared/storage/storage_adapter.py
Layer: Shared Storage Foundation
Milestone: NPP-M004 — Storage Foundation
============================================================

Defines the abstract contract implemented by all storage
backends. JSON, JSONL, CSV, Supabase, PostgreSQL and future
adapters must expose the same interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .storage_result import StorageResult


class StorageAdapter(ABC):
    """Abstract base class for all storage adapters."""

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return the adapter backend name."""

    @abstractmethod
    def exists(self, path: str | Path) -> bool:
        """Return True if the target exists."""

    @abstractmethod
    def read(self, path: str | Path) -> Any:
        """Read and return data from storage."""

    @abstractmethod
    def write(
        self,
        path: str | Path,
        data: Any,
        *,
        overwrite: bool = True,
    ) -> StorageResult:
        """Write data to storage."""

    @abstractmethod
    def append(
        self,
        path: str | Path,
        data: Any,
    ) -> StorageResult:
        """Append data to storage."""

    @abstractmethod
    def delete(self, path: str | Path) -> StorageResult:
        """Delete data from storage."""

    @abstractmethod
    def list_paths(
        self,
        path: str | Path,
    ) -> list[Path]:
        """List records beneath the supplied path."""


__all__ = ["StorageAdapter"]
