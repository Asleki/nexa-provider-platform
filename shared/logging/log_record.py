"""
============================================================
Nexa Provider Platform
File: shared/logging/log_record.py
Layer: Shared Logging Foundation
Milestone: NPP-M002 — Logging Engine
============================================================

Purpose
-------
Defines the immutable structure of one log record.

Every log generated anywhere in the platform should be
represented by this object before it is written to a console,
file, database, or external logging service.
============================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from .log_levels import LogLevel


def utc_now() -> datetime:
    """
    Return the current UTC timestamp.
    """
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class LogRecord:
    """
    Represents one immutable platform log entry.
    """

    level: LogLevel
    component: str
    message: str

    event_name: str | None = None
    actor: str | None = None
    runtime_id: str | None = None
    correlation_id: str | None = None
    exception: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    record_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=utc_now)

    @property
    def record_id_string(self) -> str:
        """
        Return the record UUID as text.
        """
        return str(self.record_id)

    @property
    def timestamp_iso(self) -> str:
        """
        Return the timestamp in ISO-8601 format.
        """
        return self.timestamp.isoformat()

    @property
    def has_exception(self) -> bool:
        """
        True if this record contains exception details.
        """
        return self.exception is not None

    @property
    def has_metadata(self) -> bool:
        """
        True if additional metadata exists.
        """
        return bool(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        """
        Return a serializable dictionary.
        """

        return {
            "record_id": self.record_id_string,
            "timestamp": self.timestamp_iso,
            "level": self.level.label,
            "component": self.component,
            "message": self.message,
            "event_name": self.event_name,
            "actor": self.actor,
            "runtime_id": self.runtime_id,
            "correlation_id": self.correlation_id,
            "exception": self.exception,
            "metadata": dict(self.metadata),
        }

    def summary(self) -> str:
        """
        Return a compact human-readable summary.
        """

        return (
            f"[{self.timestamp_iso}] "
            f"[{self.level.label}] "
            f"[{self.component}] "
            f"{self.message}"
        )