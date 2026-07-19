"""
============================================================
Nexa Provider Platform
File: shared/storage/json_storage.py
Layer: Shared Storage Foundation
Milestone: NPP-M004 — Storage Foundation
============================================================

JSON storage adapter.

Provides a filesystem-backed implementation of StorageAdapter
using UTF-8 encoded JSON documents.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .storage_adapter import StorageAdapter
from .storage_errors import (
    StorageDeserializationError,
    StoragePathNotFoundError,
    StorageSerializationError,
    StorageWriteError,
)
from .storage_result import StorageResult


class JsonStorage(StorageAdapter):
    """Storage adapter backed by JSON files."""

    @property
    def backend_name(self) -> str:
        return "json"

    def exists(self, path: str | Path) -> bool:
        return Path(path).exists()

    def read(self, path: str | Path) -> Any:
        target = Path(path)

        if not target.exists():
            raise StoragePathNotFoundError(
                "JSON file does not exist.",
                operation="read",
                path=target,
                backend=self.backend_name,
            )

        try:
            with target.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            raise StorageDeserializationError(
                "Unable to deserialize JSON content.",
                operation="read",
                path=target,
                backend=self.backend_name,
            ) from exc

    def write(
        self,
        path: str | Path,
        data: Any,
        *,
        overwrite: bool = True,
    ) -> StorageResult:
        target = Path(path)

        if target.exists() and not overwrite:
            raise StorageWriteError(
                "Target JSON file already exists.",
                operation="write",
                path=target,
                backend=self.backend_name,
            )

        target.parent.mkdir(parents=True, exist_ok=True)

        try:
            with target.open("w", encoding="utf-8") as handle:
                json.dump(
                    data,
                    handle,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
        except TypeError as exc:
            raise StorageSerializationError(
                "Object is not JSON serializable.",
                operation="write",
                path=target,
                backend=self.backend_name,
            ) from exc

        return StorageResult(
            success=True,
            operation="write",
            path=target,
            records_affected=1,
            message="JSON document written successfully.",
        )

    def append(self, path: str | Path, data: Any) -> StorageResult:
        target = Path(path)

        if target.exists():
            current = self.read(target)
            if isinstance(current, list):
                current.append(data)
            else:
                current = [current, data]
        else:
            current = [data]

        return self.write(target, current, overwrite=True)

    def delete(self, path: str | Path) -> StorageResult:
        target = Path(path)

        if target.exists():
            target.unlink()

        return StorageResult(
            success=True,
            operation="delete",
            path=target,
            records_affected=1,
            message="JSON document deleted.",
        )

    def list_records(self, path: str | Path) -> list[Path]:
        target = Path(path)

        if not target.exists():
            return []

        return sorted(target.glob("*.json"))


__all__ = ["JsonStorage"]
