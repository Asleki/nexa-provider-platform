"""Aggregate immutable metadata profile associated with one registry.

The profile composes the approved registry metadata contracts. It declares
metadata only; it does not activate a registry, enforce policy, persist data,
or execute simulation or production behaviour.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType

from .registry_capability import RegistryCapability
from .registry_data_classification import RegistryDataClassification
from .registry_metadata_errors import RegistryMetadataProfileError
from .registry_provenance import RegistryProvenance
from .registry_retention import RegistryRetention
from .registry_training_eligibility import RegistryTrainingEligibility


def _normalise_datetime(value: object, name: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime or None.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise RegistryMetadataProfileError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _parse_datetime(value: object, name: str) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return _normalise_datetime(value, name)
    if not isinstance(value, str):
        raise TypeError(f"{name} must be an ISO datetime string, datetime or None.")
    normalized = value.strip()
    if not normalized:
        raise RegistryMetadataProfileError(
            f"{name} cannot be an empty datetime string."
        )
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RegistryMetadataProfileError(
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
class RegistryMetadataProfile:
    """One immutable, versioned aggregate of registry metadata declarations."""

    registry_id: str
    capabilities: tuple[RegistryCapability, ...]
    data_classification: RegistryDataClassification
    training_eligibility: RegistryTrainingEligibility
    provenance: RegistryProvenance
    retention: RegistryRetention
    profile_version: int = 1
    effective_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reviewed_at: datetime | None = None
    review_status: str = "unreviewed"
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.registry_id, str):
            raise TypeError("registry_id must be text.")
        registry_id = self.registry_id.strip()
        if not registry_id:
            raise RegistryMetadataProfileError("registry_id cannot be empty.")
        object.__setattr__(self, "registry_id", registry_id)

        if isinstance(self.capabilities, (str, bytes)):
            raise TypeError("capabilities must be an iterable of RegistryCapability values.")
        try:
            capabilities = tuple(self.capabilities)
        except TypeError as exc:
            raise TypeError(
                "capabilities must be an iterable of RegistryCapability values."
            ) from exc
        if not all(isinstance(item, RegistryCapability) for item in capabilities):
            raise TypeError("capabilities must contain RegistryCapability values.")
        codes = [item.capability_code for item in capabilities]
        if len(codes) != len(set(codes)):
            raise RegistryMetadataProfileError(
                "capability codes must be unique within a profile."
            )
        object.__setattr__(self, "capabilities", capabilities)

        component_types = (
            ("data_classification", RegistryDataClassification),
            ("training_eligibility", RegistryTrainingEligibility),
            ("provenance", RegistryProvenance),
            ("retention", RegistryRetention),
        )
        for name, expected_type in component_types:
            if not isinstance(getattr(self, name), expected_type):
                raise TypeError(f"{name} must be a {expected_type.__name__}.")

        if isinstance(self.profile_version, bool) or not isinstance(
            self.profile_version, int
        ):
            raise TypeError("profile_version must be an integer.")
        if self.profile_version < 1:
            raise RegistryMetadataProfileError("profile_version must be at least 1.")

        object.__setattr__(
            self,
            "effective_from",
            _normalise_datetime(self.effective_from, "effective_from"),
        )
        object.__setattr__(
            self,
            "reviewed_at",
            _normalise_datetime(self.reviewed_at, "reviewed_at"),
        )

        if not isinstance(self.review_status, str):
            raise TypeError("review_status must be text.")
        review_status = self.review_status.strip().lower()
        if review_status not in {"unreviewed", "approved", "rejected", "conditional"}:
            raise RegistryMetadataProfileError("unsupported review_status.")
        if review_status == "unreviewed" and self.reviewed_at is not None:
            raise RegistryMetadataProfileError(
                "unreviewed profile cannot have reviewed_at."
            )
        if review_status != "unreviewed" and self.reviewed_at is None:
            raise RegistryMetadataProfileError("reviewed profiles require reviewed_at.")
        object.__setattr__(self, "review_status", review_status)

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")
        for key in self.attributes:
            if not isinstance(key, str):
                raise TypeError("attribute keys must be text.")
            if not key.strip():
                raise RegistryMetadataProfileError("attribute keys cannot be empty.")
        frozen_attributes = {
            key.strip(): _freeze_attribute_value(value)
            for key, value in self.attributes.items()
        }
        if len(frozen_attributes) != len(self.attributes):
            raise RegistryMetadataProfileError(
                "attribute keys must remain unique after whitespace normalization."
            )
        object.__setattr__(self, "attributes", MappingProxyType(frozen_attributes))

    def to_dict(self) -> dict[str, object]:
        """Return a deeply detached representation for persistence or transport."""
        return {
            "registry_id": self.registry_id,
            "capabilities": [item.to_dict() for item in self.capabilities],
            "data_classification": self.data_classification.to_dict(),
            "training_eligibility": self.training_eligibility.to_dict(),
            "provenance": self.provenance.to_dict(),
            "retention": self.retention.to_dict(),
            "profile_version": self.profile_version,
            "effective_from": self.effective_from.isoformat(),
            "reviewed_at": (
                None if self.reviewed_at is None else self.reviewed_at.isoformat()
            ),
            "review_status": self.review_status,
            "attributes": _thaw_attribute_value(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RegistryMetadataProfile":
        """Reconstruct a profile without retaining caller-owned mutable values."""
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")

        allowed_fields = {
            "registry_id",
            "capabilities",
            "data_classification",
            "training_eligibility",
            "provenance",
            "retention",
            "profile_version",
            "effective_from",
            "reviewed_at",
            "review_status",
            "attributes",
        }
        unknown_fields = set(data) - allowed_fields
        if unknown_fields:
            names = ", ".join(sorted(str(name) for name in unknown_fields))
            raise RegistryMetadataProfileError(f"unknown profile fields: {names}.")

        payload = dict(data)
        try:
            raw_capabilities = payload["capabilities"]
            if isinstance(raw_capabilities, (str, bytes)):
                raise TypeError("capabilities must be an iterable of mappings.")
            payload["capabilities"] = tuple(
                item
                if isinstance(item, RegistryCapability)
                else RegistryCapability.from_dict(item)
                for item in raw_capabilities
            )
            for field_name, expected_type in (
                ("data_classification", RegistryDataClassification),
                ("training_eligibility", RegistryTrainingEligibility),
                ("provenance", RegistryProvenance),
                ("retention", RegistryRetention),
            ):
                raw_value = payload[field_name]
                if not isinstance(raw_value, expected_type):
                    payload[field_name] = expected_type.from_dict(raw_value)
            payload["effective_from"] = _parse_datetime(
                payload["effective_from"], "effective_from"
            )
            payload["reviewed_at"] = _parse_datetime(
                payload.get("reviewed_at"), "reviewed_at"
            )
        except KeyError as exc:
            raise RegistryMetadataProfileError(
                f"missing required profile field: {exc.args[0]}."
            ) from exc

        return cls(**payload)


__all__ = ["RegistryMetadataProfile"]
