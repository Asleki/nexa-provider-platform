"""
============================================================
Nexa Provider Platform
File: shared/logging/log_manager.py
Layer: Shared Logging Foundation
Milestone: NPP-M002 — Logging Engine
============================================================

Purpose
-------
Coordinates all Logger instances used across the Nexa Provider
Platform.

The Log Manager:

- creates component-specific loggers;
- returns the same logger when a component requests it again;
- applies a shared minimum logging level;
- registers shared handlers across all loggers;
- updates existing loggers when configuration changes;
- provides safe status information;
- supports clean logging-engine initialization and shutdown.

Important
---------
The Log Manager does not contain business logic.

Business and provider modules request a Logger from this manager
and use that Logger to emit structured LogRecord objects.
============================================================
"""

from __future__ import annotations

from collections.abc import Iterable
from threading import RLock
from typing import Any

from .log_formatter import DEFAULT_LOG_FORMATTER, LogFormatter
from .log_levels import DEFAULT_LOG_LEVEL, LogLevel
from .log_record import LogRecord
from .logger import LogHandler, Logger


class LogManagerError(RuntimeError):
    """
    Raised when the Log Manager cannot complete an operation.
    """


class LogManager:
    """
    Creates, stores, and coordinates platform Logger instances.

    One LogManager should normally be used for one running Nexa
    Provider Platform process.
    """

    def __init__(
        self,
        *,
        minimum_level: LogLevel = DEFAULT_LOG_LEVEL,
        formatter: LogFormatter | None = None,
    ) -> None:
        if not isinstance(minimum_level, LogLevel):
            raise LogManagerError(
                "minimum_level must be a LogLevel value."
            )

        self._minimum_level = minimum_level
        self._formatter = formatter or DEFAULT_LOG_FORMATTER

        self._loggers: dict[str, Logger] = {}
        self._shared_handlers: list[LogHandler] = []

        self._initialized = False
        self._shutdown = False

        self._lock = RLock()

    @property
    def minimum_level(self) -> LogLevel:
        """
        Return the shared minimum logging level.
        """

        return self._minimum_level

    @property
    def formatter(self) -> LogFormatter:
        """
        Return the formatter assigned to newly created loggers.
        """

        return self._formatter

    @property
    def is_initialized(self) -> bool:
        """
        Return True after initialization has completed.
        """

        return self._initialized

    @property
    def is_shutdown(self) -> bool:
        """
        Return True after the manager has been shut down.
        """

        return self._shutdown

    @property
    def logger_count(self) -> int:
        """
        Return the number of managed component loggers.
        """

        with self._lock:
            return len(self._loggers)

    @property
    def component_names(self) -> tuple[str, ...]:
        """
        Return the normalized names of managed components.
        """

        with self._lock:
            return tuple(sorted(self._loggers.keys()))

    @property
    def shared_handler_count(self) -> int:
        """
        Return the number of shared handlers.
        """

        with self._lock:
            return len(self._shared_handlers)

    def initialize(self) -> None:
        """
        Initialize the Logging Engine.

        Initialization is idempotent. Calling it more than once
        does not create duplicate loggers or handlers.
        """

        with self._lock:
            if self._shutdown:
                raise LogManagerError(
                    "The Log Manager cannot be initialized after "
                    "shutdown."
                )

            if self._initialized:
                return

            self._initialized = True

        logger = self.get_logger("logging")

        logger.info(
            "Logging Engine initialized",
            event_name="LOGGING_ENGINE_INITIALIZED",
            actor="SYSTEM",
            metadata={
                "minimum_level": self._minimum_level.label,
                "managed_loggers": self.logger_count,
                "shared_handlers": self.shared_handler_count,
            },
        )

    def get_logger(
        self,
        component: str,
    ) -> Logger:
        """
        Return the Logger assigned to a component.

        The same Logger instance is returned whenever the same
        normalized component name is requested.

        Examples
        --------
        runtime_logger = manager.get_logger("Runtime")
        identity_logger = manager.get_logger("National Identity")
        """

        normalized_name = self._normalize_component_name(component)

        with self._lock:
            if self._shutdown:
                raise LogManagerError(
                    "Cannot obtain a logger because the Log Manager "
                    "has been shut down."
                )

            existing_logger = self._loggers.get(normalized_name)

            if existing_logger is not None:
                return existing_logger

            logger = Logger(
                component=component.strip(),
                minimum_level=self._minimum_level,
                formatter=self._formatter,
            )

            for handler in self._shared_handlers:
                logger.add_handler(handler)

            self._loggers[normalized_name] = logger

            return logger

    def has_logger(
        self,
        component: str,
    ) -> bool:
        """
        Return True when a component Logger already exists.
        """

        normalized_name = self._normalize_component_name(component)

        with self._lock:
            return normalized_name in self._loggers

    def set_minimum_level(
        self,
        level: LogLevel,
    ) -> None:
        """
        Change the shared minimum logging level.

        The new level is applied to all existing loggers and to
        any Logger created later.
        """

        if not isinstance(level, LogLevel):
            raise LogManagerError(
                "Logging level must be a LogLevel value."
            )

        with self._lock:
            self._ensure_active()

            previous_level = self._minimum_level
            self._minimum_level = level

            for logger in self._loggers.values():
                logger.minimum_level = level

        logging_logger = self.get_logger("logging")

        logging_logger.notice(
            "Minimum logging level changed",
            event_name="LOG_LEVEL_CHANGED",
            actor="SYSTEM",
            metadata={
                "previous_level": previous_level.label,
                "current_level": level.label,
            },
        )

    def add_shared_handler(
        self,
        handler: LogHandler,
    ) -> None:
        """
        Add a handler to every managed Logger.

        The handler is also added automatically to Loggers created
        after this call.

        Examples of future shared handlers include:

        - file writer;
        - database writer;
        - monitoring adapter;
        - remote log transport.
        """

        if not callable(handler):
            raise LogManagerError(
                "Shared log handler must be callable."
            )

        with self._lock:
            self._ensure_active()

            if handler in self._shared_handlers:
                return

            self._shared_handlers.append(handler)

            for logger in self._loggers.values():
                logger.add_handler(handler)

    def remove_shared_handler(
        self,
        handler: LogHandler,
    ) -> None:
        """
        Remove a shared handler from every managed Logger.
        """

        with self._lock:
            self._ensure_active()

            if handler not in self._shared_handlers:
                return

            self._shared_handlers.remove(handler)

            for logger in self._loggers.values():
                logger.remove_handler(handler)

    def apply_handlers(
        self,
        handlers: Iterable[LogHandler],
    ) -> None:
        """
        Register multiple shared handlers.
        """

        for handler in handlers:
            self.add_shared_handler(handler)

    def emit_system_log(
        self,
        level: LogLevel,
        message: str,
        *,
        event_name: str | None = None,
        actor: str = "SYSTEM",
        runtime_id: str | None = None,
        correlation_id: str | None = None,
        exception: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LogRecord:
        """
        Emit a record through the central Logging component.

        This is useful for messages concerning the Logging Engine
        itself rather than one specific business component.
        """

        logger = self.get_logger("logging")

        return logger.log(
            level,
            message,
            event_name=event_name,
            actor=actor,
            runtime_id=runtime_id,
            correlation_id=correlation_id,
            exception=exception,
            metadata=metadata,
        )

    def status(self) -> dict[str, Any]:
        """
        Return a safe, serializable Logging Engine summary.
        """

        with self._lock:
            return {
                "initialized": self._initialized,
                "shutdown": self._shutdown,
                "minimum_level": self._minimum_level.label,
                "logger_count": len(self._loggers),
                "components": sorted(self._loggers.keys()),
                "shared_handler_count": len(
                    self._shared_handlers
                ),
                "formatter": type(self._formatter).__name__,
            }

    def status_summary(self) -> str:
        """
        Return a human-readable Logging Engine summary.
        """

        status = self.status()

        components = (
            ", ".join(status["components"])
            if status["components"]
            else "None"
        )

        return "\n".join(
            [
                "=" * 56,
                "Nexa Provider Platform — Logging Engine",
                (
                    "State: Shutdown"
                    if status["shutdown"]
                    else (
                        "State: Initialized"
                        if status["initialized"]
                        else "State: Created"
                    )
                ),
                f"Minimum level: {status['minimum_level']}",
                f"Managed loggers: {status['logger_count']}",
                f"Components: {components}",
                (
                    "Shared handlers: "
                    f"{status['shared_handler_count']}"
                ),
                f"Formatter: {status['formatter']}",
                "=" * 56,
            ]
        )

    def shutdown(self) -> None:
        """
        Shut down the Logging Engine.

        After shutdown, no new Loggers or handlers may be created
        through this manager.
        """

        with self._lock:
            if self._shutdown:
                return

            should_log = self._initialized
            logging_logger = self._loggers.get("logging")

        if should_log and logging_logger is not None:
            logging_logger.info(
                "Logging Engine shutting down",
                event_name="LOGGING_ENGINE_SHUTDOWN",
                actor="SYSTEM",
                metadata={
                    "managed_loggers": self.logger_count,
                    "shared_handlers": self.shared_handler_count,
                },
            )

        with self._lock:
            self._initialized = False
            self._shutdown = True

            self._loggers.clear()
            self._shared_handlers.clear()

    def _ensure_active(self) -> None:
        """
        Ensure the manager has not been shut down.

        The caller must already hold the manager lock.
        """

        if self._shutdown:
            raise LogManagerError(
                "The Log Manager has already been shut down."
            )

    @staticmethod
    def _normalize_component_name(
        component: str,
    ) -> str:
        """
        Validate and normalize a component name.
        """

        if not isinstance(component, str):
            raise LogManagerError(
                "Logger component name must be text."
            )

        normalized_name = " ".join(
            component.strip().lower().split()
        )

        if not normalized_name:
            raise LogManagerError(
                "Logger component name cannot be empty."
            )

        return normalized_name


def create_log_manager(
    *,
    minimum_level: LogLevel = DEFAULT_LOG_LEVEL,
    formatter: LogFormatter | None = None,
) -> LogManager:
    """
    Public factory for creating a Log Manager.
    """

    return LogManager(
        minimum_level=minimum_level,
        formatter=formatter,
    )