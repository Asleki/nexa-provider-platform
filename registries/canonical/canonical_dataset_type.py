"""Extensible semantic type for canonical datasets.

The type describes what a dataset represents (for example authoritative,
derived, snapshot, export, simulation seed, or training evidence) without
creating a closed platform-wide enum.  Future domains may introduce richer
semantic types without changing this foundation.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*)+$")
_MAX_NAME: Final[int] = 200
_MAX_DESCRIPTION: Final[int] = 2_000


class CanonicalDatasetTypeError(ValueError):
    """Raised when a canonical-dataset type is structurally invalid."""


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


def _required(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text.")
    normalised = value.strip()
    if not normalised:
        raise CanonicalDatasetTypeError(f"{name} cannot be empty.")
    return normalised


@dataclass(frozen=True, slots=True)
class CanonicalDatasetType:
    """Stable semantic identity for one extensible canonical-dataset type."""

    dataset_type_id: str
    dataset_type_code: str
    dataset_type_name: str
    description: str = ""
    version: int = 1
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        type_id = _required("dataset_type_id", self.dataset_type_id)
        if not _ID_PATTERN.fullmatch(type_id):
            raise CanonicalDatasetTypeError(
                "dataset_type_id must start with a letter or digit and contain only "
                "letters, digits, '.', '_', ':' or '-'."
            )
        object.__setattr__(self, "dataset_type_id", type_id)

        code = _required("dataset_type_code", self.dataset_type_code).upper()
        if not _CODE_PATTERN.fullmatch(code):
            raise CanonicalDatasetTypeError(
                "dataset_type_code must be a hierarchical dotted code with at least "
                "two uppercase semantic segments."
            )
        object.__setattr__(self, "dataset_type_code", code)

        name = _required("dataset_type_name", self.dataset_type_name)
        if len(name) > _MAX_NAME:
            raise CanonicalDatasetTypeError(f"dataset_type_name cannot exceed {_MAX_NAME} characters.")
        object.__setattr__(self, "dataset_type_name", name)

        if not isinstance(self.description, str):
            raise TypeError("description must be text.")
        description = self.description.strip()
        if len(description) > _MAX_DESCRIPTION:
            raise CanonicalDatasetTypeError(f"description cannot exceed {_MAX_DESCRIPTION} characters.")
        object.__setattr__(self, "description", description)

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < 1:
            raise CanonicalDatasetTypeError("version must be at least 1.")

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")
        normalised: dict[str, object] = {}
        for key, value in self.attributes.items():
            if not isinstance(key, str):
                raise TypeError("attribute keys must be text.")
            key = key.strip()
            if not key:
                raise CanonicalDatasetTypeError("attribute keys cannot be empty.")
            if key in normalised:
                raise CanonicalDatasetTypeError(
                    "attribute keys must remain unique after whitespace normalization."
                )
            normalised[key] = _freeze(value)
        object.__setattr__(self, "attributes", MappingProxyType(normalised))

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_type_id": self.dataset_type_id,
            "dataset_type_code": self.dataset_type_code,
            "dataset_type_name": self.dataset_type_name,
            "description": self.description,
            "version": self.version,
            "attributes": _thaw(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "CanonicalDatasetType":
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {"dataset_type_id", "dataset_type_code", "dataset_type_name", "description", "version", "attributes"}
        unknown = set(data) - allowed
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise CanonicalDatasetTypeError(f"unknown canonical dataset type fields: {names}.")
        try:
            return cls(**dict(data))
        except TypeError as exc:
            if "required positional argument" in str(exc):
                raise CanonicalDatasetTypeError("missing required canonical dataset type field.") from exc
            raise


__all__ = ["CanonicalDatasetType", "CanonicalDatasetTypeError"]
