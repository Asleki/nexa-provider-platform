"""
============================================================
Nexa Provider Platform
File: shared/runtime/operation_runtime.py
Layer: Shared Runtime Extension
Milestone: M009.11.A — PostgreSQL Live Connectivity Smoke Test
============================================================

Purpose
-------
Defines the two operational data runtimes that must remain
unambiguous throughout NPP and NexiLabs:

- simulation
- production

This is intentionally distinct from RuntimeEnvironment, which
represents deployment environments such as development, testing,
staging, and production.

The contract is small so later registries, events, APIs, caches,
read models, and database adapters can reference one stable runtime
identity without embedding domain data or changing existing record
identifiers.
============================================================
"""

from __future__ import annotations

from enum import Enum
from typing import Final


ENV_OPERATION_RUNTIME_MODE: Final[str] = "NPP_RUNTIME_MODE"


class OperationRuntimeMode(str, Enum):
    """Operational data runtime used by NPP domain records."""

    SIMULATION = "simulation"
    PRODUCTION = "production"

    @classmethod
    def parse(cls, value: object) -> "OperationRuntimeMode":
        """Normalize and validate an operational runtime value."""

        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError("runtime mode must be text.")

        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("runtime mode cannot be empty.")

        try:
            return cls(normalized)
        except ValueError as exc:
            valid = ", ".join(mode.value for mode in cls)
            raise ValueError(
                f"unsupported runtime mode {value!r}; valid modes: {valid}."
            ) from exc


SUPPORTED_OPERATION_RUNTIME_MODES: Final[tuple[str, ...]] = tuple(
    mode.value for mode in OperationRuntimeMode
)


__all__ = [
    "ENV_OPERATION_RUNTIME_MODE",
    "OperationRuntimeMode",
    "SUPPORTED_OPERATION_RUNTIME_MODES",
]
