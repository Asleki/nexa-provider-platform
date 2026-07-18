"""
============================================================
Nexa Provider Platform
Package: shared.runtime
Layer: Shared Runtime Foundation
Milestone: NPP-M001 — Core Foundation
============================================================

Purpose
-------
Public exports for the Runtime Engine.

Other platform modules should import runtime functionality
through this package whenever practical.
============================================================
"""

from .runtime_config import (
    LogLevel,
    RuntimeConfig,
    RuntimeConfigurationError,
    RuntimeEnvironment,
    StorageBackend,
    load_runtime_config,
)

from .runtime_context import (
    RuntimeContext,
    RuntimeContextError,
    RuntimeState,
    create_runtime_context,
)

from .runtime_manager import (
    RuntimeComponent,
    RuntimeManager,
    RuntimeManagerError,
    create_runtime_manager,
)

__all__ = [
    "LogLevel",
    "RuntimeConfig",
    "RuntimeConfigurationError",
    "RuntimeEnvironment",
    "StorageBackend",
    "load_runtime_config",
    "RuntimeContext",
    "RuntimeContextError",
    "RuntimeState",
    "create_runtime_context",
    "RuntimeComponent",
    "RuntimeManager",
    "RuntimeManagerError",
    "create_runtime_manager",
]