"""Immutable immediate provenance declaration for one relationship instance.

The contract records where one cross-registry relationship immediately came
from. It does not become an audit trail, provenance graph, trust engine,
evidence store, approval workflow, migration engine, or event publisher.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Final

from registries.metadata.registry_provenance_source_type import (
    RegistryProvenanceSourceType,
)

_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_RUNTIME_MODE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_MAX_SOURCE_SYSTEM_LENGTH: Final[int] = 255
_MAX_REFERENCE_LENGTH: Final[int] = 512
_MAX_GENERATOR_NAME_LENGTH: Final[int] = 255
_MAX_GENERATOR_VERSION_LENGTH: Final[int] = 255
_MAX_REASON_LENGTH: Final[int] = 2_000


class RelationshipProvenanceError(ValueError):
    """Raised when relationship provenance is structurally invalid."""


def _text(value: object, name: str, *, maximum_length: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text.")
    normalised = value.strip()
    if len(normalised) > maximum_length:
        raise RelationshipProvenanceError(
            f"{name} cannot exceed {maximum_length} characters."
        )
    return normalised


def _required_identifier(value: object, name: str) -> str:
    normalised = _text(value, name, maximum_length=256)
    if not normalised:
        raise RelationshipProvenanceError(f"{name} cannot be empty.")
    if not _ID_PATTERN.fullmatch(normalised):
        raise RelationshipProvenanceError(
            f"{name} must start with a letter or digit and contain only letters, "
            "digits, '.', '_', ':' or '-'."
        )
    return normalised


def _datetime(value: object, name: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime or None.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise RelationshipProvenanceError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _parse_datetime(value: object, name: str) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return _datetime(value, name)
    if not isinstance(value, str):
        raise TypeError(f"{name} must be an ISO datetime string, datetime or None.")
    normalised = value.strip()
    if not normalised:
        raise RelationshipProvenanceError(f"{name} cannot be an empty datetime string.")
    try:
        parsed = datetime.fromisoformat(normalised.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RelationshipProvenanceError(
            f"{name} must be a valid ISO datetime string."
        ) from exc
    return _datetime(parsed, name)


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        frozen: dict[object, object] = {}
        for key, nested in value.items():
            try:
                hash(key)
            except TypeError as exc:
                raise TypeError("attribute mapping keys must be hashable.") from exc
            frozen[key] = _freeze(nested)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item) for item in value)
    return value


def _thaw(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, frozenset):
        return [_thaw(item) for item in sorted(value, key=repr)]
    return value


@dataclass(frozen=True, slots=True)
class RelationshipProvenance:
    """One immutable, versioned immediate-origin declaration."""

    provenance_id: str
    relationship_id: str
    relationship_version: int
    runtime_mode: str
    source_type: RegistryProvenanceSourceType
    source_system: str
    source_reference: str = ""
    source_actor_id: str = ""
    source_institution_id: str = ""
    source_event_id: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    generated: bool = False
    generator_name: str = ""
    generator_version: str = ""
    generation_batch_id: str = ""
    generation_seed_reference: str = ""
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    verified: bool = False
    verified_at: datetime | None = None
    verification_reference: str = ""
    version: int = 1
    attributes: Mapping[str, object] = field(default_factory=dict)
    reason: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "provenance_id", _required_identifier(self.provenance_id, "provenance_id"))
        object.__setattr__(self, "relationship_id", _required_identifier(self.relationship_id, "relationship_id"))

        if isinstance(self.relationship_version, bool) or not isinstance(self.relationship_version, int):
            raise TypeError("relationship_version must be an integer.")
        if self.relationship_version < 1:
            raise RelationshipProvenanceError("relationship_version must be at least 1.")

        runtime_mode = _text(self.runtime_mode, "runtime_mode", maximum_length=64).lower()
        if not runtime_mode:
            raise RelationshipProvenanceError("runtime_mode cannot be empty.")
        if not _RUNTIME_MODE_PATTERN.fullmatch(runtime_mode):
            raise RelationshipProvenanceError(
                "runtime_mode must start with a lowercase letter and contain only "
                "lowercase letters, digits, '_' or '-'."
            )
        object.__setattr__(self, "runtime_mode", runtime_mode)

        try:
            source_type = RegistryProvenanceSourceType.from_value(self.source_type)
        except ValueError as exc:
            raise RelationshipProvenanceError(str(exc)) from exc
        object.__setattr__(self, "source_type", source_type)

        limits = {
            "source_system": _MAX_SOURCE_SYSTEM_LENGTH,
            "source_reference": _MAX_REFERENCE_LENGTH,
            "source_actor_id": _MAX_REFERENCE_LENGTH,
            "source_institution_id": _MAX_REFERENCE_LENGTH,
            "source_event_id": _MAX_REFERENCE_LENGTH,
            "correlation_id": _MAX_REFERENCE_LENGTH,
            "causation_id": _MAX_REFERENCE_LENGTH,
            "generator_name": _MAX_GENERATOR_NAME_LENGTH,
            "generator_version": _MAX_GENERATOR_VERSION_LENGTH,
            "generation_batch_id": _MAX_REFERENCE_LENGTH,
            "generation_seed_reference": _MAX_REFERENCE_LENGTH,
            "verification_reference": _MAX_REFERENCE_LENGTH,
            "reason": _MAX_REASON_LENGTH,
        }
        for name, limit in limits.items():
            object.__setattr__(self, name, _text(getattr(self, name), name, maximum_length=limit))

        if source_type is RegistryProvenanceSourceType.UNKNOWN:
            if self.source_system:
                raise RelationshipProvenanceError("UNKNOWN provenance cannot claim a source_system.")
            if not self.reason:
                raise RelationshipProvenanceError("UNKNOWN provenance requires a reason describing the missing origin.")
        elif not self.source_system:
            raise RelationshipProvenanceError("source_system cannot be empty for known provenance.")

        if not isinstance(self.generated, bool):
            raise TypeError("generated must be a boolean.")
        if not isinstance(self.verified, bool):
            raise TypeError("verified must be a boolean.")

        generation_values = (
            self.generator_name,
            self.generator_version,
            self.generation_batch_id,
            self.generation_seed_reference,
        )
        if source_type is RegistryProvenanceSourceType.SIMULATION_GENERATOR:
            if not self.generated:
                raise RelationshipProvenanceError("SIMULATION_GENERATOR provenance requires generated=True.")
        elif self.generated:
            raise RelationshipProvenanceError("generated=True requires source_type=SIMULATION_GENERATOR.")

        if self.generated:
            if not (self.generator_name or self.generation_batch_id or self.generation_seed_reference):
                raise RelationshipProvenanceError("generated provenance requires generator or generation reference information.")
            if self.generator_version and not self.generator_name:
                raise RelationshipProvenanceError("generator_version requires generator_name.")
        elif any(generation_values):
            raise RelationshipProvenanceError("non-generated provenance cannot contain generator details.")

        if source_type in (RegistryProvenanceSourceType.IMPORT, RegistryProvenanceSourceType.DERIVED) and not (
            self.source_reference or self.source_event_id or self.reason
        ):
            raise RelationshipProvenanceError(
                f"{source_type.name} provenance requires a source reference, source event or reason."
            )

        recorded_at = _datetime(self.recorded_at, "recorded_at")
        verified_at = _datetime(self.verified_at, "verified_at")
        object.__setattr__(self, "recorded_at", recorded_at)
        object.__setattr__(self, "verified_at", verified_at)

        if source_type is RegistryProvenanceSourceType.UNKNOWN and self.verified:
            raise RelationshipProvenanceError("UNKNOWN provenance cannot be marked verified.")
        if self.verified and verified_at is None and not self.verification_reference:
            raise RelationshipProvenanceError("verified provenance requires verified_at or verification_reference.")
        if not self.verified and (verified_at is not None or self.verification_reference):
            raise RelationshipProvenanceError("unverified provenance cannot contain verification details.")
        if verified_at is not None and verified_at < recorded_at:
            raise RelationshipProvenanceError("verified_at cannot be earlier than recorded_at.")

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < 1:
            raise RelationshipProvenanceError("version must be at least 1.")

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")
        normalised_attributes: dict[str, object] = {}
        for key, value in self.attributes.items():
            if not isinstance(key, str):
                raise TypeError("attribute keys must be text.")
            normalised_key = key.strip()
            if not normalised_key:
                raise RelationshipProvenanceError("attribute keys cannot be empty.")
            if normalised_key in normalised_attributes:
                raise RelationshipProvenanceError("attribute keys must remain unique after whitespace normalization.")
            normalised_attributes[normalised_key] = _freeze(value)
        object.__setattr__(self, "attributes", MappingProxyType(normalised_attributes))

    def to_dict(self) -> dict[str, object]:
        return {
            "provenance_id": self.provenance_id,
            "relationship_id": self.relationship_id,
            "relationship_version": self.relationship_version,
            "runtime_mode": self.runtime_mode,
            "source_type": self.source_type.value,
            "source_system": self.source_system,
            "source_reference": self.source_reference,
            "source_actor_id": self.source_actor_id,
            "source_institution_id": self.source_institution_id,
            "source_event_id": self.source_event_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "generated": self.generated,
            "generator_name": self.generator_name,
            "generator_version": self.generator_version,
            "generation_batch_id": self.generation_batch_id,
            "generation_seed_reference": self.generation_seed_reference,
            "recorded_at": self.recorded_at.isoformat(),
            "verified": self.verified,
            "verified_at": None if self.verified_at is None else self.verified_at.isoformat(),
            "verification_reference": self.verification_reference,
            "version": self.version,
            "attributes": _thaw(self.attributes),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RelationshipProvenance":
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {
            "provenance_id", "relationship_id", "relationship_version", "runtime_mode",
            "source_type", "source_system", "source_reference", "source_actor_id",
            "source_institution_id", "source_event_id", "correlation_id", "causation_id",
            "generated", "generator_name", "generator_version", "generation_batch_id",
            "generation_seed_reference", "recorded_at", "verified", "verified_at",
            "verification_reference", "version", "attributes", "reason",
        }
        unknown = set(data) - allowed
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise RelationshipProvenanceError(f"unknown relationship provenance fields: {names}.")
        payload = dict(data)
        for name in ("recorded_at", "verified_at"):
            if name in payload:
                payload[name] = _parse_datetime(payload[name], name)
        try:
            return cls(**payload)
        except TypeError as exc:
            if "required positional argument" in str(exc):
                raise RelationshipProvenanceError("missing required relationship provenance field.") from exc
            raise


__all__ = ["RelationshipProvenance", "RelationshipProvenanceError"]
