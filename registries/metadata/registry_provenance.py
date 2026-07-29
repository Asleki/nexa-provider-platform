"""Immutable immediate source-lineage declaration for registry metadata.

The contract states where one registry-level fact or record immediately came
from.  It deliberately does not become a full provenance graph, audit trail,
trust decision, ownership statement, migration engine, or dataset manifest.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Final

from .registry_metadata_errors import RegistryProvenanceError
from .registry_provenance_source_type import RegistryProvenanceSourceType

_MAX_SOURCE_SYSTEM_LENGTH: Final[int] = 255
_MAX_REFERENCE_LENGTH: Final[int] = 512
_MAX_GENERATOR_NAME_LENGTH: Final[int] = 255
_MAX_GENERATOR_VERSION_LENGTH: Final[int] = 255
_MAX_REASON_LENGTH: Final[int] = 2_000


def _normalise_text(
    value: object,
    name: str,
    *,
    maximum_length: int,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text.")
    normalized = value.strip()
    if len(normalized) > maximum_length:
        raise RegistryProvenanceError(
            f"{name} cannot exceed {maximum_length} characters."
        )
    return normalized


def _normalise_datetime(value: object, name: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime or None.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise RegistryProvenanceError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _parse_datetime(value: object, name: str) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return _normalise_datetime(value, name)
    if not isinstance(value, str):
        raise TypeError(f"{name} must be an ISO datetime string, datetime or None.")
    normalized = value.strip()
    if not normalized:
        raise RegistryProvenanceError(f"{name} cannot be an empty datetime string.")
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RegistryProvenanceError(
            f"{name} must be a valid ISO datetime string."
        ) from exc
    return _normalise_datetime(parsed, name)


def _freeze_attribute_value(value: object) -> object:
    if isinstance(value, Mapping):
        frozen: dict[object, object] = {}
        for key, nested_value in value.items():
            try:
                hash(key)
            except TypeError as exc:
                raise TypeError("attribute mapping keys must be hashable.") from exc
            frozen[key] = _freeze_attribute_value(nested_value)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_attribute_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze_attribute_value(item) for item in value)
    return value


def _thaw_attribute_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_attribute_value(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_thaw_attribute_value(item) for item in value]
    if isinstance(value, frozenset):
        return [
            _thaw_attribute_value(item)
            for item in sorted(value, key=lambda item: repr(item))
        ]
    return value


@dataclass(frozen=True, slots=True)
class RegistryProvenance:
    """One immutable and versioned immediate-provenance declaration."""

    source_type: RegistryProvenanceSourceType
    source_system: str
    source_reference: str = ""
    source_actor_id: str = ""
    source_institution_id: str = ""
    source_event_id: str = ""
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
        try:
            source_type = RegistryProvenanceSourceType.from_value(self.source_type)
        except ValueError as exc:
            raise RegistryProvenanceError(str(exc)) from exc
        object.__setattr__(self, "source_type", source_type)

        text_limits = {
            "source_system": _MAX_SOURCE_SYSTEM_LENGTH,
            "source_reference": _MAX_REFERENCE_LENGTH,
            "source_actor_id": _MAX_REFERENCE_LENGTH,
            "source_institution_id": _MAX_REFERENCE_LENGTH,
            "source_event_id": _MAX_REFERENCE_LENGTH,
            "generator_name": _MAX_GENERATOR_NAME_LENGTH,
            "generator_version": _MAX_GENERATOR_VERSION_LENGTH,
            "generation_batch_id": _MAX_REFERENCE_LENGTH,
            "generation_seed_reference": _MAX_REFERENCE_LENGTH,
            "verification_reference": _MAX_REFERENCE_LENGTH,
            "reason": _MAX_REASON_LENGTH,
        }
        for name, maximum_length in text_limits.items():
            object.__setattr__(
                self,
                name,
                _normalise_text(
                    getattr(self, name),
                    name,
                    maximum_length=maximum_length,
                ),
            )

        if self.source_type is RegistryProvenanceSourceType.UNKNOWN:
            if self.source_system:
                raise RegistryProvenanceError(
                    "UNKNOWN provenance cannot claim a source_system."
                )
            if not self.reason:
                raise RegistryProvenanceError(
                    "UNKNOWN provenance requires a reason describing the missing origin."
                )
        elif not self.source_system:
            raise RegistryProvenanceError(
                "source_system cannot be empty for known provenance."
            )

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
        if self.source_type is RegistryProvenanceSourceType.SIMULATION_GENERATOR:
            if not self.generated:
                raise RegistryProvenanceError(
                    "SIMULATION_GENERATOR provenance requires generated=True."
                )
        elif self.generated:
            raise RegistryProvenanceError(
                "generated=True requires source_type=SIMULATION_GENERATOR."
            )

        if self.generated:
            if not (
                self.generator_name
                or self.generation_batch_id
                or self.generation_seed_reference
            ):
                raise RegistryProvenanceError(
                    "generated provenance requires generator or generation "
                    "reference information."
                )
            if self.generator_version and not self.generator_name:
                raise RegistryProvenanceError(
                    "generator_version requires generator_name."
                )
        elif any(generation_values):
            raise RegistryProvenanceError(
                "non-generated provenance cannot contain generator details."
            )

        if self.source_type in (
            RegistryProvenanceSourceType.IMPORT,
            RegistryProvenanceSourceType.DERIVED,
        ) and not (self.source_reference or self.source_event_id or self.reason):
            raise RegistryProvenanceError(
                f"{self.source_type.name} provenance requires a source reference, "
                "source event or reason."
            )

        recorded_at = _normalise_datetime(self.recorded_at, "recorded_at")
        verified_at = _normalise_datetime(self.verified_at, "verified_at")
        object.__setattr__(self, "recorded_at", recorded_at)
        object.__setattr__(self, "verified_at", verified_at)

        if self.source_type is RegistryProvenanceSourceType.UNKNOWN and self.verified:
            raise RegistryProvenanceError(
                "UNKNOWN provenance cannot be marked verified."
            )
        if self.verified and verified_at is None and not self.verification_reference:
            raise RegistryProvenanceError(
                "verified provenance requires verified_at or verification_reference."
            )
        if not self.verified and (
            verified_at is not None or self.verification_reference
        ):
            raise RegistryProvenanceError(
                "unverified provenance cannot contain verification details."
            )
        if verified_at is not None and verified_at < recorded_at:
            raise RegistryProvenanceError(
                "verified_at cannot be earlier than recorded_at."
            )

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < 1:
            raise RegistryProvenanceError("version must be at least 1.")

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")
        normalized_attributes: dict[str, object] = {}
        for key, value in self.attributes.items():
            if not isinstance(key, str):
                raise TypeError("attribute keys must be text.")
            normalized_key = key.strip()
            if not normalized_key:
                raise RegistryProvenanceError("attribute keys cannot be empty.")
            if normalized_key in normalized_attributes:
                raise RegistryProvenanceError(
                    "attribute keys must remain unique after whitespace normalization."
                )
            normalized_attributes[normalized_key] = _freeze_attribute_value(value)
        object.__setattr__(
            self,
            "attributes",
            MappingProxyType(normalized_attributes),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deeply detached representation for persistence or transport."""
        return {
            "source_type": self.source_type.value,
            "source_system": self.source_system,
            "source_reference": self.source_reference,
            "source_actor_id": self.source_actor_id,
            "source_institution_id": self.source_institution_id,
            "source_event_id": self.source_event_id,
            "generated": self.generated,
            "generator_name": self.generator_name,
            "generator_version": self.generator_version,
            "generation_batch_id": self.generation_batch_id,
            "generation_seed_reference": self.generation_seed_reference,
            "recorded_at": self.recorded_at.isoformat(),
            "verified": self.verified,
            "verified_at": (
                None if self.verified_at is None else self.verified_at.isoformat()
            ),
            "verification_reference": self.verification_reference,
            "version": self.version,
            "attributes": _thaw_attribute_value(self.attributes),
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RegistryProvenance":
        """Reconstruct provenance from a detached persistence mapping."""
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        values = dict(data)
        if "recorded_at" in values:
            values["recorded_at"] = _parse_datetime(
                values["recorded_at"],
                "recorded_at",
            )
        if "verified_at" in values:
            values["verified_at"] = _parse_datetime(
                values["verified_at"],
                "verified_at",
            )
        return cls(**values)


__all__ = ["RegistryProvenance"]
