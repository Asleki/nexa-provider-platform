"""
============================================================
Nexa Provider Platform
File: shared/storage/csv_storage.py
Layer: Shared Storage Foundation
Milestone: NPP-M004 — Storage Foundation
============================================================

CSV storage adapter.

Implements the StorageAdapter contract using UTF-8 encoded CSV
files. Intended for structured imports, exports, reporting, and
tabular datasets.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .storage_adapter import StorageAdapter
from .storage_errors import (
    StoragePathNotFoundError,
    StorageValidationError,
)
from .storage_result import StorageResult


class CsvStorage(StorageAdapter):
    """Storage adapter backed by CSV files."""

    @property
    def backend_name(self) -> str:
        return "csv"

    def exists(self, path: str | Path) -> bool:
        return Path(path).exists()

    def read(self, path: str | Path) -> list[dict[str, str]]:
        target = Path(path)

        if not target.exists():
            raise StoragePathNotFoundError(
                "CSV file does not exist.",
                operation="read",
                path=target,
                backend=self.backend_name,
            )

        with target.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def write(
        self,
        path: str | Path,
        data: Any,
        *,
        overwrite: bool = True,
    ) -> StorageResult:
        if not isinstance(data, list):
            raise StorageValidationError(
                "CSV write expects a list of dictionaries.",
                operation="write",
                path=path,
                backend=self.backend_name,
            )

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        mode = "w" if overwrite else "x"

        rows = [row for row in data if isinstance(row, dict)]

        fieldnames: list[str] = []
        for row in rows:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(str(key))

        with target.open(mode, encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        return StorageResult(
            success=True,
            operation="write",
            path=target,
            records_affected=len(rows),
            message="CSV document written successfully.",
        )

    def append(self, path: str | Path, data: Any) -> StorageResult:
        target = Path(path)

        if not isinstance(data, dict):
            raise StorageValidationError(
                "CSV append expects a dictionary.",
                operation="append",
                path=target,
                backend=self.backend_name,
            )

        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists():
            with target.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = list(reader.fieldnames or [])
        else:
            fieldnames = list(data.keys())

        for key in data.keys():
            if key not in fieldnames:
                fieldnames.append(key)

        write_header = not target.exists() or target.stat().st_size == 0

        with target.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerow(data)

        return StorageResult(
            success=True,
            operation="append",
            path=target,
            records_affected=1,
            message="CSV record appended successfully.",
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
            message="CSV document deleted.",
        )

    def list_paths(self, path: str | Path) -> list[Path]:
        target = Path(path)
        if not target.exists():
            return []
        return sorted(target.glob("*.csv"))


__all__ = ["CsvStorage"]
