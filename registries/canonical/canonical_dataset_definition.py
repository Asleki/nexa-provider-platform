"""Immutable definition of one canonical dataset.

The definition declares identity, semantics, authority, schema, version,
runtime separation and immediate lineage.  It does not contain dataset records,
resolve storage, merge identities, publish events or grant access.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Final

from .canonical_dataset_reference import CanonicalDatasetReference
from .canonical_dataset_type import CanonicalDatasetType

_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*)+$")
_RUNTIME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_MAX_NAME: Final[int] = 200
_MAX_DESCRIPTION: Final[int] = 2_000


class CanonicalDatasetDefinitionError(ValueError):
    """Raised when a canonical dataset definition is structurally invalid."""


def _required(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text.")
    value = value.strip()
    if not value:
        raise CanonicalDatasetDefinitionError(f"{name} cannot be empty.")
    return value


def _time(value: object, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise CanonicalDatasetDefinitionError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _parse_time(value: object, name: str) -> datetime:
    if isinstance(value, datetime):
        return _time(value, name)
    if not isinstance(value, str):
        raise TypeError(f"{name} must be an ISO datetime string or datetime.")
    try:
        return _time(datetime.fromisoformat(value.strip().replace("Z", "+00:00")), name)
    except ValueError as exc:
        raise CanonicalDatasetDefinitionError(f"{name} must be a valid ISO datetime string.") from exc


def _freeze(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(nested) for key, nested in value.items()})
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
class CanonicalDatasetDefinition:
    """Storage-neutral declaration of one canonical dataset version."""

    dataset_id: str
    dataset_code: str
    dataset_name: str
    dataset_type: CanonicalDatasetType
    authority_registry_id: str
    record_type_code: str
    schema_id: str
    schema_version: int
    dataset_version: int
    runtime_mode: str
    created_at: datetime
    description: str = ""
    source_datasets: tuple[CanonicalDatasetReference, ...] = ()
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        dataset_id = _required("dataset_id", self.dataset_id)
        authority = _required("authority_registry_id", self.authority_registry_id)
        schema_id = _required("schema_id", self.schema_id)
        for name, value in (("dataset_id", dataset_id), ("authority_registry_id", authority), ("schema_id", schema_id)):
            if not _ID_PATTERN.fullmatch(value):
                raise CanonicalDatasetDefinitionError(f"{name} has an invalid identifier format.")
            object.__setattr__(self, name, value)

        for name in ("dataset_code", "record_type_code"):
            value = _required(name, getattr(self, name)).upper()
            if not _CODE_PATTERN.fullmatch(value):
                raise CanonicalDatasetDefinitionError(f"{name} must be a hierarchical dotted semantic code.")
            object.__setattr__(self, name, value)

        name = _required("dataset_name", self.dataset_name)
        if len(name) > _MAX_NAME:
            raise CanonicalDatasetDefinitionError(f"dataset_name cannot exceed {_MAX_NAME} characters.")
        object.__setattr__(self, "dataset_name", name)

        if not isinstance(self.dataset_type, CanonicalDatasetType):
            raise TypeError("dataset_type must be a CanonicalDatasetType.")
        for name in ("schema_version", "dataset_version"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer.")
            if value < 1:
                raise CanonicalDatasetDefinitionError(f"{name} must be at least 1.")

        runtime = _required("runtime_mode", self.runtime_mode).lower()
        if not _RUNTIME_PATTERN.fullmatch(runtime):
            raise CanonicalDatasetDefinitionError("runtime_mode has an invalid format.")
        object.__setattr__(self, "runtime_mode", runtime)
        object.__setattr__(self, "created_at", _time(self.created_at, "created_at"))

        if not isinstance(self.description, str):
            raise TypeError("description must be text.")
        description = self.description.strip()
        if len(description) > _MAX_DESCRIPTION:
            raise CanonicalDatasetDefinitionError(f"description cannot exceed {_MAX_DESCRIPTION} characters.")
        object.__setattr__(self, "description", description)

        if isinstance(self.source_datasets, (str, bytes)) or not isinstance(self.source_datasets, Iterable):
            raise TypeError("source_datasets must be an iterable of CanonicalDatasetReference values.")
        sources = tuple(self.source_datasets)
        if any(not isinstance(item, CanonicalDatasetReference) for item in sources):
            raise TypeError("source_datasets must contain only CanonicalDatasetReference values.")
        identities = [(item.dataset_id, item.dataset_version, item.runtime_mode) for item in sources]
        if len(identities) != len(set(identities)):
            raise CanonicalDatasetDefinitionError("source_datasets must be unique.")
        if any(item.dataset_id == dataset_id and item.dataset_version == self.dataset_version and item.runtime_mode == runtime for item in sources):
            raise CanonicalDatasetDefinitionError("a dataset cannot cite itself as an immediate source.")
        object.__setattr__(self, "source_datasets", sources)

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")
        normalised: dict[str, object] = {}
        for key, value in self.attributes.items():
            if not isinstance(key, str):
                raise TypeError("attribute keys must be text.")
            key = key.strip()
            if not key:
                raise CanonicalDatasetDefinitionError("attribute keys cannot be empty.")
            if key in normalised:
                raise CanonicalDatasetDefinitionError("attribute keys must remain unique after whitespace normalization.")
            normalised[key] = _freeze(value)
        object.__setattr__(self, "attributes", MappingProxyType(normalised))

    @property
    def reference(self) -> CanonicalDatasetReference:
        return CanonicalDatasetReference(self.dataset_id, self.dataset_version, self.runtime_mode)

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id, "dataset_code": self.dataset_code,
            "dataset_name": self.dataset_name, "dataset_type": self.dataset_type.to_dict(),
            "authority_registry_id": self.authority_registry_id, "record_type_code": self.record_type_code,
            "schema_id": self.schema_id, "schema_version": self.schema_version,
            "dataset_version": self.dataset_version, "runtime_mode": self.runtime_mode,
            "created_at": self.created_at.isoformat(), "description": self.description,
            "source_datasets": [item.to_dict() for item in self.source_datasets],
            "attributes": _thaw(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "CanonicalDatasetDefinition":
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {"dataset_id", "dataset_code", "dataset_name", "dataset_type", "authority_registry_id", "record_type_code", "schema_id", "schema_version", "dataset_version", "runtime_mode", "created_at", "description", "source_datasets", "attributes"}
        unknown = set(data) - allowed
        if unknown:
            raise CanonicalDatasetDefinitionError(f"unknown canonical dataset definition fields: {', '.join(sorted(map(str, unknown)))}.")
        payload = dict(data)
        try:
            if not isinstance(payload["dataset_type"], CanonicalDatasetType):
                payload["dataset_type"] = CanonicalDatasetType.from_dict(payload["dataset_type"])
            payload["created_at"] = _parse_time(payload["created_at"], "created_at")
            payload["source_datasets"] = tuple(item if isinstance(item, CanonicalDatasetReference) else CanonicalDatasetReference.from_dict(item) for item in payload.get("source_datasets", ()))
            return cls(**payload)
        except KeyError as exc:
            raise CanonicalDatasetDefinitionError(f"missing required canonical dataset definition field: {exc.args[0]}.") from exc
        except TypeError as exc:
            if "required positional argument" in str(exc):
                raise CanonicalDatasetDefinitionError("missing required canonical dataset definition field.") from exc
            raise


__all__ = ["CanonicalDatasetDefinition", "CanonicalDatasetDefinitionError"]
