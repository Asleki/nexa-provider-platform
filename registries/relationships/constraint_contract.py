"""Immutable structural constraint contracts for registry relationships.

M008.16.4 declares storage-neutral policies for endpoint compatibility,
self-reference, duplicate pairs, cardinality and runtime applicability.  It does
not resolve registry records, count persisted relationships, enforce lifecycle,
traverse graphs, publish events, or apply domain-specific eligibility rules.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Final

from .relationship_type import RelationshipType

_CONSTRAINT_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$"
)
_CONSTRAINT_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*)+$"
)
_REGISTRY_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$"
)
_RUNTIME_MODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9_-]{0,63}$"
)
_MAX_DESCRIPTION_LENGTH: Final[int] = 1000


class RelationshipConstraintError(ValueError):
    """Raised when a relationship-constraint contract is invalid."""


class RelationshipSelfReferencePolicy(str, Enum):
    """Whether one record may occupy both endpoints of a relationship."""

    ALLOW = "allow"
    PROHIBIT = "prohibit"


class RelationshipDuplicatePolicy(str, Enum):
    """Whether an identical typed source-target pair may already exist."""

    ALLOW = "allow"
    PROHIBIT = "prohibit"


@dataclass(frozen=True, slots=True)
class RelationshipCardinality:
    """Inclusive count bounds for one endpoint side.

    ``maximum=None`` means that the upper bound is unbounded.
    """

    minimum: int = 0
    maximum: int | None = None

    def __post_init__(self) -> None:
        _validate_count("minimum", self.minimum)
        if self.maximum is not None:
            _validate_count("maximum", self.maximum)
            if self.maximum < self.minimum:
                raise RelationshipConstraintError(
                    "maximum cannot be less than minimum."
                )

    def allows_count(self, count: int) -> bool:
        """Return whether ``count`` lies inside the inclusive bounds."""
        _validate_count("count", count)
        if count < self.minimum:
            return False
        return self.maximum is None or count <= self.maximum

    def to_dict(self) -> dict[str, object]:
        return {"minimum": self.minimum, "maximum": self.maximum}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RelationshipCardinality":
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {"minimum", "maximum"}
        unknown = set(data) - allowed
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise RelationshipConstraintError(
                f"unknown relationship cardinality fields: {names}."
            )
        try:
            return cls(**dict(data))
        except TypeError as exc:
            if "required positional argument" in str(exc):
                raise RelationshipConstraintError(
                    "missing required relationship cardinality field."
                ) from exc
            raise


@dataclass(frozen=True, slots=True)
class RelationshipConstraint:
    """Immutable structural policy for one semantic relationship type."""

    constraint_id: str
    constraint_code: str
    relationship_type: RelationshipType
    allowed_source_registry_ids: tuple[str, ...] = ()
    allowed_target_registry_ids: tuple[str, ...] = ()
    source_cardinality: RelationshipCardinality = field(default_factory=RelationshipCardinality)
    target_cardinality: RelationshipCardinality = field(default_factory=RelationshipCardinality)
    self_reference_policy: RelationshipSelfReferencePolicy = (
        RelationshipSelfReferencePolicy.PROHIBIT
    )
    duplicate_policy: RelationshipDuplicatePolicy = RelationshipDuplicatePolicy.PROHIBIT
    runtime_modes: tuple[str, ...] = ("production", "simulation")
    description: str = ""
    version: int = 1

    def __post_init__(self) -> None:
        constraint_id = _required("constraint_id", self.constraint_id)
        if not _CONSTRAINT_ID_PATTERN.fullmatch(constraint_id):
            raise RelationshipConstraintError(
                "constraint_id must start with a letter or digit and contain only "
                "letters, digits, '.', '_', ':' or '-'."
            )
        object.__setattr__(self, "constraint_id", constraint_id)

        constraint_code = _required("constraint_code", self.constraint_code).upper()
        if not _CONSTRAINT_CODE_PATTERN.fullmatch(constraint_code):
            raise RelationshipConstraintError(
                "constraint_code must be a hierarchical dotted code with at least "
                "two uppercase semantic segments."
            )
        object.__setattr__(self, "constraint_code", constraint_code)

        if not isinstance(self.relationship_type, RelationshipType):
            raise TypeError("relationship_type must be a RelationshipType.")

        object.__setattr__(
            self,
            "allowed_source_registry_ids",
            _normalise_registry_ids(
                "allowed_source_registry_ids", self.allowed_source_registry_ids
            ),
        )
        object.__setattr__(
            self,
            "allowed_target_registry_ids",
            _normalise_registry_ids(
                "allowed_target_registry_ids", self.allowed_target_registry_ids
            ),
        )

        if not isinstance(self.source_cardinality, RelationshipCardinality):
            raise TypeError("source_cardinality must be a RelationshipCardinality.")
        if not isinstance(self.target_cardinality, RelationshipCardinality):
            raise TypeError("target_cardinality must be a RelationshipCardinality.")
        if not isinstance(self.self_reference_policy, RelationshipSelfReferencePolicy):
            raise TypeError(
                "self_reference_policy must be a RelationshipSelfReferencePolicy."
            )
        if not isinstance(self.duplicate_policy, RelationshipDuplicatePolicy):
            raise TypeError("duplicate_policy must be a RelationshipDuplicatePolicy.")

        object.__setattr__(
            self, "runtime_modes", _normalise_runtime_modes(self.runtime_modes)
        )

        if not isinstance(self.description, str):
            raise TypeError("description must be text.")
        description = self.description.strip()
        if len(description) > _MAX_DESCRIPTION_LENGTH:
            raise RelationshipConstraintError(
                f"description cannot exceed {_MAX_DESCRIPTION_LENGTH} characters."
            )
        object.__setattr__(self, "description", description)

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < 1:
            raise RelationshipConstraintError("version must be at least 1.")

    def allows_source_registry(self, registry_id: str) -> bool:
        normalised = _normalise_registry_id("registry_id", registry_id)
        return (
            not self.allowed_source_registry_ids
            or normalised in self.allowed_source_registry_ids
        )

    def allows_target_registry(self, registry_id: str) -> bool:
        normalised = _normalise_registry_id("registry_id", registry_id)
        return (
            not self.allowed_target_registry_ids
            or normalised in self.allowed_target_registry_ids
        )

    def applies_to_runtime(self, runtime_mode: str) -> bool:
        normalised = _normalise_runtime_mode("runtime_mode", runtime_mode)
        return normalised in self.runtime_modes

    def to_dict(self) -> dict[str, object]:
        """Return a detached, deterministic transport representation."""
        return {
            "constraint_id": self.constraint_id,
            "constraint_code": self.constraint_code,
            "relationship_type": self.relationship_type.to_dict(),
            "allowed_source_registry_ids": list(self.allowed_source_registry_ids),
            "allowed_target_registry_ids": list(self.allowed_target_registry_ids),
            "source_cardinality": self.source_cardinality.to_dict(),
            "target_cardinality": self.target_cardinality.to_dict(),
            "self_reference_policy": self.self_reference_policy.value,
            "duplicate_policy": self.duplicate_policy.value,
            "runtime_modes": list(self.runtime_modes),
            "description": self.description,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RelationshipConstraint":
        """Rebuild a constraint without retaining caller-owned containers."""
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {
            "constraint_id",
            "constraint_code",
            "relationship_type",
            "allowed_source_registry_ids",
            "allowed_target_registry_ids",
            "source_cardinality",
            "target_cardinality",
            "self_reference_policy",
            "duplicate_policy",
            "runtime_modes",
            "description",
            "version",
        }
        unknown = set(data) - allowed
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise RelationshipConstraintError(
                f"unknown relationship constraint fields: {names}."
            )
        payload = dict(data)
        required = {"constraint_id", "constraint_code", "relationship_type"}
        missing = required - set(payload)
        if missing:
            names = ", ".join(sorted(missing))
            raise RelationshipConstraintError(
                f"missing required relationship constraint fields: {names}."
            )
        try:
            if not isinstance(payload["relationship_type"], RelationshipType):
                payload["relationship_type"] = RelationshipType.from_dict(
                    payload["relationship_type"]
                )
            for field_name in ("source_cardinality", "target_cardinality"):
                if field_name in payload and not isinstance(
                    payload[field_name], RelationshipCardinality
                ):
                    payload[field_name] = RelationshipCardinality.from_dict(
                        payload[field_name]
                    )
            if "self_reference_policy" in payload and not isinstance(
                payload["self_reference_policy"], RelationshipSelfReferencePolicy
            ):
                payload["self_reference_policy"] = RelationshipSelfReferencePolicy(
                    payload["self_reference_policy"]
                )
            if "duplicate_policy" in payload and not isinstance(
                payload["duplicate_policy"], RelationshipDuplicatePolicy
            ):
                payload["duplicate_policy"] = RelationshipDuplicatePolicy(
                    payload["duplicate_policy"]
                )
        except ValueError as exc:
            if isinstance(exc, RelationshipConstraintError):
                raise
            raise RelationshipConstraintError(
                "unknown relationship constraint policy value."
            ) from exc
        return cls(**payload)


def _required(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text.")
    normalised = value.strip()
    if not normalised:
        raise RelationshipConstraintError(f"{name} cannot be empty.")
    return normalised


def _validate_count(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer.")
    if value < 0:
        raise RelationshipConstraintError(f"{name} cannot be negative.")


def _normalise_registry_id(name: str, value: object) -> str:
    registry_id = _required(name, value)
    if not _REGISTRY_ID_PATTERN.fullmatch(registry_id):
        raise RelationshipConstraintError(
            f"{name} must start with a letter or digit and contain only letters, "
            "digits, '.', '_', ':' or '-'."
        )
    return registry_id


def _normalise_registry_ids(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TypeError(f"{name} must be an iterable of registry IDs.")
    normalised = [_normalise_registry_id(name, value) for value in values]
    if len(set(normalised)) != len(normalised):
        raise RelationshipConstraintError(
            f"{name} cannot contain duplicate registry IDs."
        )
    return tuple(sorted(normalised))


def _normalise_runtime_mode(name: str, value: object) -> str:
    runtime_mode = _required(name, value).lower()
    if not _RUNTIME_MODE_PATTERN.fullmatch(runtime_mode):
        raise RelationshipConstraintError(
            f"{name} must start with a lowercase letter and contain only lowercase "
            "letters, digits, '_' or '-'."
        )
    return runtime_mode


def _normalise_runtime_modes(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TypeError("runtime_modes must be an iterable of runtime modes.")
    normalised = [_normalise_runtime_mode("runtime_mode", value) for value in values]
    if not normalised:
        raise RelationshipConstraintError("runtime_modes cannot be empty.")
    if len(set(normalised)) != len(normalised):
        raise RelationshipConstraintError(
            "runtime_modes cannot contain duplicate runtime modes."
        )
    return tuple(sorted(normalised))


__all__ = [
    "RelationshipCardinality",
    "RelationshipConstraint",
    "RelationshipConstraintError",
    "RelationshipDuplicatePolicy",
    "RelationshipSelfReferencePolicy",
]
