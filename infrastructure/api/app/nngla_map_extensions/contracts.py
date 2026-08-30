"""Generic additive NNGLA national-map extension contracts.

Compatibility maintenance for the locked P006.7.11.15.6-.15.8.1 map stack.
The seam does not implement a geographic layer.  It provides a constrained,
append-only composition surface so later governed layers can wrap the existing
repository/service pair without reopening locked REGION or CITY modules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


_ALLOWED_RUNTIME_MODES = frozenset({"simulation", "production"})


@dataclass(frozen=True, slots=True)
class NNGLAMapExtensionContext:
    """Immutable composition state handed from one additive layer to the next."""

    pool: Any
    runtime_mode: str
    map_repository: Any
    map_read_service: Any
    resources: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.pool is None:
            raise TypeError("pool is required")
        normalized_runtime = str(self.runtime_mode).strip().lower()
        if normalized_runtime not in _ALLOWED_RUNTIME_MODES:
            raise ValueError("runtime_mode must be simulation or production")
        if self.map_repository is None:
            raise TypeError("map_repository is required")
        if self.map_read_service is None:
            raise TypeError("map_read_service is required")
        repository_runtime = str(getattr(self.map_repository, "runtime_mode", "")).strip().lower()
        if repository_runtime != normalized_runtime:
            raise ValueError("map_repository runtime_mode must match extension context")
        service_repository = getattr(self.map_read_service, "repository", None)
        if service_repository is not self.map_repository:
            raise ValueError("map_read_service must be bound to map_repository")
        object.__setattr__(self, "runtime_mode", normalized_runtime)
        object.__setattr__(self, "resources", MappingProxyType(dict(self.resources)))

    def with_layer(
        self,
        *,
        map_repository: Any,
        map_read_service: Any,
        resources: Mapping[str, Any] | None = None,
    ) -> "NNGLAMapExtensionContext":
        """Return the next immutable context after one additive extension layer."""

        merged_resources = dict(self.resources)
        if resources:
            for key, value in resources.items():
                normalized = str(key).strip()
                if not normalized:
                    raise ValueError("resource keys must be non-empty")
                if value is None:
                    raise TypeError(f"resource {normalized!r} cannot be None")
                merged_resources[normalized] = value
        return NNGLAMapExtensionContext(
            pool=self.pool,
            runtime_mode=self.runtime_mode,
            map_repository=map_repository,
            map_read_service=map_read_service,
            resources=merged_resources,
        )


__all__ = ["NNGLAMapExtensionContext"]
