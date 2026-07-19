
"""
============================================================
Nexa Provider Platform
File: shared/storage/storage_paths.py
Layer: Shared Storage Foundation
Milestone: NPP-M004 — Storage Foundation
============================================================

Purpose
-------
Centralizes storage-path resolution and validation for the
Storage Foundation.

This module ensures all local storage operations remain inside
the configured storage root and provides common helpers for
creating and resolving storage locations.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .storage_errors import StoragePathTraversalError


@dataclass(frozen=True, slots=True)
class StoragePaths:
    """Represents the approved storage root."""

    storage_root: Path

    def resolve(self, *parts: str) -> Path:
        """Resolve a path beneath the storage root."""

        candidate = (self.storage_root.joinpath(*parts)).resolve()
        root = self.storage_root.resolve()

        if root != candidate and root not in candidate.parents:
            raise StoragePathTraversalError(
                "Resolved path escapes the configured storage root.",
                operation="resolve",
                path=candidate,
            )

        return candidate

    def ensure_directory(self, *parts: str) -> Path:
        """Create a directory beneath the storage root if needed."""

        directory = self.resolve(*parts)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def exists(self, *parts: str) -> bool:
        """Return True when the resolved path exists."""

        return self.resolve(*parts).exists()

    def relative(self, path: str | Path) -> Path:
        """Return a path relative to the storage root."""

        resolved = Path(path).resolve()
        root = self.storage_root.resolve()

        if root != resolved and root not in resolved.parents:
            raise StoragePathTraversalError(
                "Path is outside the configured storage root.",
                operation="relative",
                path=resolved,
            )

        return resolved.relative_to(root)


__all__ = [
    "StoragePaths",
]
