"""
============================================================
Nexa Provider Platform
File: registries/governance/registry_lifecycle.py
Layer: Master Registry Foundation
Milestone: NPP-M008.8 — Registry Lifecycle
============================================================

Storage-neutral execution façade for registry-definition lifecycle changes.
It validates a requested transition, preserves stable registry identity and
unrelated definition fields, and returns a new immutable BaseRegistry for a
real transition.

The lifecycle does not persist changes, authorize actors, publish events,
write audits, expose HTTP APIs, or cascade changes to related registries.
============================================================
"""

from __future__ import annotations

from registries.core import BaseRegistry, RegistryDefinition, RegistryStatus

from .lifecycle_errors import RegistryLifecycleInputError
from .lifecycle_policy import RegistryLifecyclePolicy
from .lifecycle_result import RegistryLifecycleResult


class RegistryLifecycle:
    """Apply deterministic, immutable registry-definition transitions."""

    def __init__(
        self,
        policy: RegistryLifecyclePolicy | None = None,
    ) -> None:
        if policy is not None and not isinstance(
            policy,
            RegistryLifecyclePolicy,
        ):
            raise RegistryLifecycleInputError(
                "policy must be a RegistryLifecyclePolicy instance.",
                field="policy",
                context={"actual_type": type(policy).__name__},
            )
        self._policy = policy or RegistryLifecyclePolicy()

    @property
    def policy(self) -> RegistryLifecyclePolicy:
        """Return the lifecycle transition policy."""

        return self._policy

    def is_operational(self, registry: BaseRegistry) -> bool:
        """Return whether a registry is active for normal operation."""

        normalized = self._require_registry(registry)
        return self.policy.is_operational(normalized.status)

    def can_transition(
        self,
        registry: BaseRegistry,
        target_status: RegistryStatus | str,
    ) -> bool:
        """Return whether a registry may move to the requested status."""

        normalized = self._require_registry(registry)
        return self.policy.can_transition(
            normalized.status,
            target_status,
        )

    def transition(
        self,
        registry: BaseRegistry,
        target_status: RegistryStatus | str,
    ) -> RegistryLifecycleResult:
        """Apply one approved immutable lifecycle transition."""

        source = self._require_registry(registry)
        previous_status, requested_status = self.policy.require_transition(
            source.status,
            target_status,
            registry_id=source.registry_id,
            allow_noop=True,
        )

        if previous_status is requested_status:
            return RegistryLifecycleResult(
                registry=source,
                previous_status=previous_status,
                current_status=requested_status,
                changed=False,
                message=(
                    "Registry already has the requested lifecycle status; "
                    "no state change was required."
                ),
                metadata={"version_changed": False},
            )

        values = source.to_dict()
        values["status"] = requested_status.value
        values["version"] = source.version + 1
        updated_definition = RegistryDefinition.from_dict(values)
        updated_registry = BaseRegistry.from_definition(updated_definition)

        return RegistryLifecycleResult(
            registry=updated_registry,
            previous_status=previous_status,
            current_status=requested_status,
            changed=True,
            message=(
                "Registry lifecycle transition completed successfully."
            ),
            metadata={
                "previous_version": source.version,
                "current_version": updated_registry.version,
                "version_changed": True,
            },
        )

    @staticmethod
    def _require_registry(registry: BaseRegistry) -> BaseRegistry:
        if not isinstance(registry, BaseRegistry):
            raise RegistryLifecycleInputError(
                "registry must be a BaseRegistry instance.",
                field="registry",
                context={"actual_type": type(registry).__name__},
            )
        return registry


__all__ = ["RegistryLifecycle"]
