"""
============================================================
Nexa Provider Platform
File: shared/logging/log_formatter.py
Layer: Shared Logging Foundation
Milestone: NPP-M002 — Logging Engine
============================================================

Purpose
-------
Formats LogRecord objects into different output formats.

Supported formats:

- Human-readable text
- Compact text
- JSON-ready dictionary

The formatter never creates or stores logs.
Its only responsibility is presentation.
============================================================
"""

from __future__ import annotations

import json
from typing import Any

from .log_record import LogRecord


class LogFormatter:
    """
    Formats platform log records.
    """

    def format(self, record: LogRecord) -> str:
        """
        Produce the standard human-readable format.
        """

        lines = [
            "=" * 72,
            f"Timestamp      : {record.timestamp_iso}",
            f"Level          : {record.level.label}",
            f"Component      : {record.component}",
            f"Message        : {record.message}",
        ]

        if record.event_name:
            lines.append(
                f"Event          : {record.event_name}"
            )

        if record.actor:
            lines.append(
                f"Actor          : {record.actor}"
            )

        if record.runtime_id:
            lines.append(
                f"Runtime ID     : {record.runtime_id}"
            )

        if record.correlation_id:
            lines.append(
                f"Correlation ID : {record.correlation_id}"
            )

        if record.exception:
            lines.append(
                f"Exception      : {record.exception}"
            )

        if record.metadata:
            lines.append("Metadata:")

            for key, value in sorted(record.metadata.items()):
                lines.append(f"  • {key}: {value}")

        lines.append("=" * 72)

        return "\n".join(lines)

    def format_compact(
        self,
        record: LogRecord,
    ) -> str:
        """
        Produce a single-line representation.
        """

        return (
            f"[{record.timestamp_iso}] "
            f"[{record.level.short_label}] "
            f"[{record.component}] "
            f"{record.message}"
        )

    def format_json(
        self,
        record: LogRecord,
        *,
        indent: int = 2,
    ) -> str:
        """
        Produce formatted JSON.
        """

        return json.dumps(
            record.to_dict(),
            indent=indent,
            ensure_ascii=False,
            default=str,
        )

    def format_dictionary(
        self,
        record: LogRecord,
    ) -> dict[str, Any]:
        """
        Return a dictionary representation.
        """

        return record.to_dict()


DEFAULT_LOG_FORMATTER = LogFormatter()