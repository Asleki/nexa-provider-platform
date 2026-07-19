"""
============================================================
Nexa Provider Platform
File: shared/storage/storage_result.py
Layer: Shared Storage Foundation
Milestone: NPP-M004 — Storage Foundation
============================================================

Represents the standardized result returned by storage
operations. It provides a consistent contract for reads,
writes, deletes, imports, exports, and future storage adapters.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class StorageResult:
    """
    Standard result returned by Storage Foundation operations.
    """

    success: bool
    operation: str
    path: Path | None = None
    records_affected: int = 0
    message: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def failed(self) -> bool:
        """Return True when the operation failed."""
        return not self.success

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result into a dictionary."""
        return {
            "success": self.success,
            "operation": self.operation,
            "path": str(self.path) if self.path else None,
            "records_affected": self.records_affected,
            "message": self.message,
            "metadata": dict(self.metadata),
        }


__all__ = [
    "StorageResult",
]
