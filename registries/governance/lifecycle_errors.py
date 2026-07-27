"""
============================================================
Nexa Provider Platform
File: registries/governance/lifecycle_errors.py
Layer: Master Registry Foundation
Milestone: NPP-M008.8 — Registry Lifecycle
============================================================

Lifecycle-specific, transport-neutral exceptions for registry-definition
state inspection and transition failures.

The errors preserve the shared RegistryError diagnostic shape and do not
perform persistence, authorization, event publication, audit recording, or
API translation.
============================================================
"""

from __future__ import annotations

from collections.abc import Mapping

from registries.core import RegistryStatus
from registries.errors.registry_error import RegistryStateError


def _status_value(value: RegistryStatus | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, RegistryStatus):
        return value.value
    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized or None
    return str(value)


class RegistryLifecycleError(RegistryStateError):
    """Base exception for Registry Lifecycle failures."""

    error_code = "NPP-REGISTRY-LIFECYCLE-001"

    def __init__(
        self,
        message: str,
        *,
        registry_id: str | None = None,
        current_status: RegistryStatus | str | None = None,
        target_status: RegistryStatus | str | None = None,
        field: str | None = None,
        context: Mapping[str, object] | None = None,
    ) -> None:
        lifecycle_context = dict(context or {})
        current_value = _status_value(current_status)
        target_value = _status_value(target_status)
        if current_value is not None:
            lifecycle_context.setdefault("current_status", current_value)
        if target_value is not None:
            lifecycle_context.setdefault("target_status", target_value)
        super().__init__(
            message,
            code=self.error_code,
            field=field,
            resource_reference=registry_id,
            context=lifecycle_context,
        )

    @property
    def registry_id(self) -> str | None:
        """Return the affected registry identifier, when available."""

        return self.resource_reference

    @property
    def current_status(self) -> str | None:
        """Return the normalized current lifecycle status."""

        value = self.context.get("current_status")
        return value if isinstance(value, str) else None

    @property
    def target_status(self) -> str | None:
        """Return the normalized requested lifecycle status."""

        value = self.context.get("target_status")
        return value if isinstance(value, str) else None


class RegistryLifecycleInputError(RegistryLifecycleError, ValueError):
    """Raised when lifecycle input cannot be safely interpreted."""

    error_code = "NPP-REGISTRY-LIFECYCLE-010"


class RegistryLifecycleTransitionError(RegistryLifecycleError, ValueError):
    """Raised when a requested registry lifecycle transition is disallowed."""

    error_code = "NPP-REGISTRY-LIFECYCLE-020"


class RegistryLifecycleTerminalStateError(RegistryLifecycleTransitionError):
    """Raised when a transition is requested from a terminal state."""

    error_code = "NPP-REGISTRY-LIFECYCLE-021"


__all__ = [
    "RegistryLifecycleError",
    "RegistryLifecycleInputError",
    "RegistryLifecycleTerminalStateError",
    "RegistryLifecycleTransitionError",
]
