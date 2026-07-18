"""
============================================================
Nexa Provider Platform
File: shared/logging/logger.py
Layer: Shared Logging Foundation
Milestone: NPP-M002 — Logging Engine
============================================================

Purpose
-------
Provides the primary logging interface for the platform.

The Logger creates LogRecord objects and forwards them to one
or more handlers.

By default, logs are written to the console.

Future handlers may include:

- Log files
- Audit storage
- Database
- Cloud logging
- Monitoring systems
============================================================
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .log_formatter import DEFAULT_LOG_FORMATTER, LogFormatter
from .log_levels import LogLevel
from .log_record import LogRecord


LogHandler = Callable[[LogRecord], None]


class Logger:
    """
    Main platform logger.
    """

    def __init__(
        self,
        component: str,
        *,
        minimum_level: LogLevel = LogLevel.default(),
        formatter: LogFormatter | None = None,
    ) -> None:

        self._component = component.strip()
        self._minimum_level = minimum_level
        self._formatter = formatter or DEFAULT_LOG_FORMATTER
        self._handlers: list[LogHandler] = []

        self.add_handler(self._console_handler)

    @property
    def component(self) -> str:
        return self._component

    @property
    def minimum_level(self) -> LogLevel:
        return self._minimum_level

    @minimum_level.setter
    def minimum_level(
        self,
        value: LogLevel,
    ) -> None:
        self._minimum_level = value

    def add_handler(
        self,
        handler: LogHandler,
    ) -> None:
        """
        Register a log handler.
        """

        if handler not in self._handlers:
            self._handlers.append(handler)

    def remove_handler(
        self,
        handler: LogHandler,
    ) -> None:
        """
        Remove a log handler.
        """

        if handler in self._handlers:
            self._handlers.remove(handler)

    def log(
        self,
        level: LogLevel,
        message: str,
        *,
        event_name: str | None = None,
        actor: str | None = None,
        runtime_id: str | None = None,
        correlation_id: str | None = None,
        exception: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LogRecord:
        """
        Create and emit a log record.
        """

        if level < self._minimum_level:
            return LogRecord(
                level=level,
                component=self._component,
                message=message,
            )

        record = LogRecord(
            level=level,
            component=self._component,
            message=message,
            event_name=event_name,
            actor=actor,
            runtime_id=runtime_id,
            correlation_id=correlation_id,
            exception=exception,
            metadata=metadata or {},
        )

        for handler in self._handlers:
            handler(record)

        return record

    def trace(self, message: str, **kwargs: Any) -> LogRecord:
        return self.log(LogLevel.TRACE, message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> LogRecord:
        return self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> LogRecord:
        return self.log(LogLevel.INFO, message, **kwargs)

    def notice(self, message: str, **kwargs: Any) -> LogRecord:
        return self.log(LogLevel.NOTICE, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> LogRecord:
        return self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> LogRecord:
        return self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> LogRecord:
        return self.log(LogLevel.CRITICAL, message, **kwargs)

    def fatal(self, message: str, **kwargs: Any) -> LogRecord:
        return self.log(LogLevel.FATAL, message, **kwargs)

    def _console_handler(
        self,
        record: LogRecord,
    ) -> None:
        """
        Default console output.
        """

        print(
            self._formatter.format_compact(record)
        )


def create_logger(
    component: str,
    *,
    minimum_level: LogLevel = LogLevel.default(),
) -> Logger:
    """
    Factory for creating platform loggers.
    """

    return Logger(
        component=component,
        minimum_level=minimum_level,
    )