"""
============================================================
Nexa Provider Platform
File: registries/governance/lifecycle_policy.py
Layer: Master Registry Foundation
Milestone: NPP-M008.8 — Registry Lifecycle
============================================================

Pure, repository-neutral transition policy for registry-definition lifecycle
states. The policy centralizes transition rules and state classification.

It does not mutate registries, persist state, authorize actors, publish
registry events, write audit records, or apply cross-registry cascades.
============================================================
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final, Mapping

from registries.core import RegistryStatus

from .lifecycle_errors import (
    RegistryLifecycleInputError,
    RegistryLifecycleTerminalStateError,
    RegistryLifecycleTransitionError,
)


_ALLOWED_TRANSITIONS: Final[Mapping[RegistryStatus, frozenset[RegistryStatus]]] = (
    MappingProxyType(
        {
            RegistryStatus.DRAFT: frozenset(
                {RegistryStatus.ACTIVE, RegistryStatus.RETIRED}
            ),
            RegistryStatus.ACTIVE: frozenset(
                {RegistryStatus.SUSPENDED, RegistryStatus.RETIRED}
            ),
            RegistryStatus.SUSPENDED: frozenset(
                {RegistryStatus.ACTIVE, RegistryStatus.RETIRED}
            ),
            RegistryStatus.RETIRED: frozenset(),
        }
    )
)

_TERMINAL_STATUSES: Final[frozenset[RegistryStatus]] = frozenset(
    {RegistryStatus.RETIRED}
)
_OPERATIONAL_STATUSES: Final[frozenset[RegistryStatus]] = frozenset(
    {RegistryStatus.ACTIVE}
)


class RegistryLifecyclePolicy:
    """Deterministic policy for registry-definition status transitions."""

    @staticmethod
    def normalize_status(
        value: RegistryStatus | str,
        *,
        field_name: str = "status",
    ) -> RegistryStatus:
        """Normalize an enum or case-insensitive serialized status."""

        if isinstance(value, RegistryStatus):
            return value
        if not isinstance(value, str):
            raise RegistryLifecycleInputError(
                f"{field_name} must be a RegistryStatus or text.",
                field=field_name,
                context={"actual_type": type(value).__name__},
            )
        normalized = value.strip().lower()
        if not normalized:
            raise RegistryLifecycleInputError(
                f"{field_name} cannot be empty.",
                field=field_name,
            )
        try:
            return RegistryStatus(normalized)
        except ValueError as exc:
            raise RegistryLifecycleInputError(
                f"Unsupported registry lifecycle status {value!r}.",
                field=field_name,
                context={"value": value},
            ) from exc

    @classmethod
    def allowed_targets(
        cls,
        current_status: RegistryStatus | str,
    ) -> tuple[RegistryStatus, ...]:
        """Return deterministic allowed targets for one state."""

        current = cls.normalize_status(
            current_status,
            field_name="current_status",
        )
        return tuple(sorted(_ALLOWED_TRANSITIONS[current], key=lambda item: item.value))

    @classmethod
    def is_terminal(cls, status: RegistryStatus | str) -> bool:
        """Return whether a state is terminal."""

        return cls.normalize_status(status) in _TERMINAL_STATUSES

    @classmethod
    def is_operational(cls, status: RegistryStatus | str) -> bool:
        """Return whether a state permits normal registry operation."""

        return cls.normalize_status(status) in _OPERATIONAL_STATUSES

    @classmethod
    def can_transition(
        cls,
        current_status: RegistryStatus | str,
        target_status: RegistryStatus | str,
        *,
        allow_noop: bool = True,
    ) -> bool:
        """Return whether the requested transition is allowed."""

        if not isinstance(allow_noop, bool):
            raise RegistryLifecycleInputError(
                "allow_noop must be a boolean.",
                field="allow_noop",
                context={"actual_type": type(allow_noop).__name__},
            )
        current = cls.normalize_status(
            current_status,
            field_name="current_status",
        )
        target = cls.normalize_status(
            target_status,
            field_name="target_status",
        )
        if current is target:
            return allow_noop
        return target in _ALLOWED_TRANSITIONS[current]

    @classmethod
    def require_transition(
        cls,
        current_status: RegistryStatus | str,
        target_status: RegistryStatus | str,
        *,
        registry_id: str | None = None,
        allow_noop: bool = True,
    ) -> tuple[RegistryStatus, RegistryStatus]:
        """Validate and return normalized current and target states."""

        current = cls.normalize_status(
            current_status,
            field_name="current_status",
        )
        target = cls.normalize_status(
            target_status,
            field_name="target_status",
        )
        if current is target:
            if allow_noop:
                return current, target
            raise RegistryLifecycleTransitionError(
                "Registry is already in the requested lifecycle state.",
                registry_id=registry_id,
                current_status=current,
                target_status=target,
                field="target_status",
            )
        if current in _TERMINAL_STATUSES:
            raise RegistryLifecycleTerminalStateError(
                "Retired registry definitions cannot transition to another state.",
                registry_id=registry_id,
                current_status=current,
                target_status=target,
                field="current_status",
            )
        if target not in _ALLOWED_TRANSITIONS[current]:
            raise RegistryLifecycleTransitionError(
                "Requested registry lifecycle transition is not allowed.",
                registry_id=registry_id,
                current_status=current,
                target_status=target,
                field="target_status",
                context={
                    "allowed_targets": tuple(
                        item.value for item in cls.allowed_targets(current)
                    )
                },
            )
        return current, target


__all__ = ["RegistryLifecyclePolicy"]
