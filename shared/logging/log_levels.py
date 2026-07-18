"""
============================================================
Nexa Provider Platform
File: shared/logging/log_levels.py
Layer: Shared Logging Foundation
Milestone: NPP-M002 — Logging Engine
============================================================

Purpose
-------
Defines the standard logging severity levels used throughout
the Nexa Provider Platform.

All platform components should use these levels to ensure
consistent logging across:

- Runtime
- Security
- Identity
- Registries
- Providers
- Synchronization
- Audit
- Simulation

Severity Order
--------------
TRACE
DEBUG
INFO
NOTICE
WARNING
ERROR
CRITICAL
FATAL
============================================================
"""

from __future__ import annotations

from enum import IntEnum


class LogLevel(IntEnum):
    """
    Standard logging severity.

    Higher numbers indicate more severe events.
    """

    TRACE = 10
    DEBUG = 20
    INFO = 30
    NOTICE = 40
    WARNING = 50
    ERROR = 60
    CRITICAL = 70
    FATAL = 80

    @property
    def label(self) -> str:
        """
        Return the display label.
        """

        return self.name

    @property
    def short_label(self) -> str:
        """
        Return the abbreviated label.
        """

        return {
            LogLevel.TRACE: "TRC",
            LogLevel.DEBUG: "DBG",
            LogLevel.INFO: "INF",
            LogLevel.NOTICE: "NTC",
            LogLevel.WARNING: "WRN",
            LogLevel.ERROR: "ERR",
            LogLevel.CRITICAL: "CRT",
            LogLevel.FATAL: "FTL",
        }[self]

    @property
    def is_error(self) -> bool:
        """
        Return True for error-level logs.
        """

        return self >= LogLevel.ERROR

    @property
    def requires_attention(self) -> bool:
        """
        Return True for logs that should attract operator attention.
        """

        return self >= LogLevel.WARNING

    @classmethod
    def from_name(cls, value: str) -> "LogLevel":
        """
        Parse a log level from text.

        Examples
        --------
        INFO
        info
        Warning
        """

        normalized = value.strip().upper()

        try:
            return cls[normalized]
        except KeyError as error:
            supported = ", ".join(level.name for level in cls)

            raise ValueError(
                f"Unknown log level {value!r}. "
                f"Supported levels: {supported}."
            ) from error

    @classmethod
    def default(cls) -> "LogLevel":
        """
        Return the platform default logging level.
        """

        return cls.INFO

    @classmethod
    def all_levels(cls) -> tuple["LogLevel", ...]:
        """
        Return every supported log level.
        """

        return tuple(cls)

    def __str__(self) -> str:
        """
        Return the display label.
        """

        return self.label


DEFAULT_LOG_LEVEL = LogLevel.default()