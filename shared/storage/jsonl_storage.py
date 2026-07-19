"""
============================================================
Nexa Provider Platform
File: shared/storage/jsonl_storage.py
Layer: Shared Storage Foundation
Milestone: NPP-M004 — Storage Foundation
============================================================

JSON Lines storage adapter.

Implements append-only storage using the JSON Lines (.jsonl)
format. Each line is an independent JSON document, making this
adapter suitable for immutable event streams, audit logs, and
synchronization queues.
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
)
from .storage_result import StorageResult


class JsonlStorage(StorageAdapter):
    """Append-oriented storage adapter for JSON Lines."""

    @property
    def backend_name(self) -> str:
        return "jsonl"

    def exists(self, path: str | Path) -> bool:
        return Path(path).exists()

    def read(self, path: str | Path) -> list[Any]:
        target = Path(path)

        if not target.exists():
            raise StoragePathNotFoundError(
                "JSONL file does not exist.",
                operation="read",
                path=target,
                backend=self.backend_name,
            )

        records: list[Any] = []

        with target.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    records.append(json.loads(text))
                except json.JSONDecodeError as exc:
                    raise StorageDeserializationError(
                        f"Invalid JSON on line {line_number}.",
                        operation="read",
                        path=target,
                        backend=self.backend_name,
                    ) from exc

        return records

    def write(
        self,
        path: str | Path,
        data: Any,
        *,
        overwrite: bool = True,
    ) -> StorageResult:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        mode = "w" if overwrite else "x"

        try:
            with target.open(mode, encoding="utf-8") as handle:
                if isinstance(data, list):
                    for item in data:
                        handle.write(json.dumps(item, ensure_ascii=False))
                        handle.write("\n")
                else:
                    handle.write(json.dumps(data, ensure_ascii=False))
                    handle.write("\n")
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
            records_affected=len(data) if isinstance(data, list) else 1,
            message="JSONL document written successfully.",
        )

    def append(self, path: str | Path, data: Any) -> StorageResult:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        try:
            with target.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(data, ensure_ascii=False))
                handle.write("\n")
        except TypeError as exc:
            raise StorageSerializationError(
                "Object is not JSON serializable.",
                operation="append",
                path=target,
                backend=self.backend_name,
            ) from exc

        return StorageResult(
            success=True,
            operation="append",
            path=target,
            records_affected=1,
            message="Record appended successfully.",
        )

    def delete(self, path: str | Path) -> StorageResult:
        target = Path(path)
        if target.exists():
            target.unlink()

        return StorageResult(
            success=True,
            operation="delete",
            path=target,
            records_affected=1,
            message="JSONL document deleted.",
        )

    def list_records(self, path: str | Path) -> list[Path]:
        target = Path(path)
        if not target.exists():
            return []
        return sorted(target.glob("*.jsonl"))


__all__ = ["JsonlStorage"]
