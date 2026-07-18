"""
============================================================
Nexa Provider Platform
Package: shared.logging
Layer: Shared Logging Foundation
Milestone: NPP-M002 — Logging Engine
============================================================

Purpose
-------
Exposes the public interface of the Nexa Provider Platform
Logging Engine.

Platform modules should import logging tools from this package
instead of importing deeply from individual implementation files.

Example
-------
from shared.logging import (
    LogLevel,
    LogManager,
    create_log_manager,
)

log_manager = create_log_manager()
log_manager.initialize()

logger = log_manager.get_logger("Runtime")
logger.info("Runtime started")
============================================================
"""

from .log_formatter import (
    DEFAULT_LOG_FORMATTER,
    LogFormatter,
)
from .log_levels import (
    DEFAULT_LOG_LEVEL,
    LogLevel,
)
from .log_manager import (
    LogManager,
    LogManagerError,
    create_log_manager,
)
from .log_record import (
    LogRecord,
    utc_now,
)
from .logger import (
    LogHandler,
    Logger,
    create_logger,
)


__all__ = [
    "DEFAULT_LOG_FORMATTER",
    "DEFAULT_LOG_LEVEL",
    "LogFormatter",
    "LogHandler",
    "LogLevel",
    "LogManager",
    "LogManagerError",
    "LogRecord",
    "Logger",
    "create_log_manager",
    "create_logger",
    "utc_now",
]