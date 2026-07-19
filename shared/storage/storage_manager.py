"""
============================================================
Nexa Provider Platform
File: shared/storage/storage_manager.py
Layer: Shared Storage Foundation
Milestone: NPP-M004 — Storage Foundation
============================================================

Coordinates storage adapters used by the platform.

The StorageManager registers adapters, selects the active
backend, and exposes a consistent API to higher layers without
binding them to a specific storage implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .storage_adapter import StorageAdapter
from .storage_errors import (
    StorageConfigurationError,
    UnsupportedStorageBackendError,
)
from .storage_result import StorageResult


class StorageManager:
    """Coordinates registered storage adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, StorageAdapter] = {}
        self._active_backend: str | None = None

    def register_adapter(
        self,
        adapter: StorageAdapter,
        *,
        make_default: bool = False,
    ) -> None:
        """Register a storage adapter."""

        self._adapters[adapter.backend_name] = adapter

        if make_default or self._active_backend is None:
            self._active_backend = adapter.backend_name

    @property
    def active_backend(self) -> str:
        """Return the active backend name."""

        if self._active_backend is None:
            raise StorageConfigurationError(
                "No storage adapter has been configured."
            )

        return self._active_backend

    def get_adapter(
        self,
        backend: str | None = None,
    ) -> StorageAdapter:
        """Return a registered adapter."""

        name = backend or self.active_backend

        try:
            return self._adapters[name]
        except KeyError as exc:
            raise UnsupportedStorageBackendError(
                f"Unknown storage backend: {name}",
                backend=name,
            ) from exc

    def exists(self, path: str | Path, *, backend: str | None = None) -> bool:
        return self.get_adapter(backend).exists(path)

    def read(self, path: str | Path, *, backend: str | None = None) -> Any:
        return self.get_adapter(backend).read(path)

    def write(
        self,
        path: str | Path,
        data: Any,
        *,
        overwrite: bool = True,
        backend: str | None = None,
    ) -> StorageResult:
        return self.get_adapter(backend).write(
            path,
            data,
            overwrite=overwrite,
        )

    def append(
        self,
        path: str | Path,
        data: Any,
        *,
        backend: str | None = None,
    ) -> StorageResult:
        return self.get_adapter(backend).append(path, data)

    def delete(
        self,
        path: str | Path,
        *,
        backend: str | None = None,
    ) -> StorageResult:
        return self.get_adapter(backend).delete(path)

    def list_paths(
        self,
        path: str | Path,
        *,
        backend: str | None = None,
    ) -> list[Path]:
        return self.get_adapter(backend).list_paths(path)

    @property
    def registered_backends(self) -> tuple[str, ...]:
        """Return registered backend names."""
        return tuple(sorted(self._adapters))


__all__ = ["StorageManager"]
