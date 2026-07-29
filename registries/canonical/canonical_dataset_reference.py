"""Immutable reference to one canonical dataset version.

A reference carries stable dataset identity, version and runtime separation.
It does not load records, authorise access, resolve storage, or imply that a
referenced dataset is public or authoritative.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_RUNTIME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


class CanonicalDatasetReferenceError(ValueError):
    """Raised when a canonical-dataset reference is structurally invalid."""


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
        raise CanonicalDatasetReferenceError(f"{name} cannot be empty.")
    return normalised


@dataclass(frozen=True, slots=True)
class CanonicalDatasetReference:
    """Stable identity of one canonical dataset version and runtime mode."""

    dataset_id: str
    dataset_version: int
    runtime_mode: str
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        dataset_id = _required("dataset_id", self.dataset_id)
        if not _ID_PATTERN.fullmatch(dataset_id):
            raise CanonicalDatasetReferenceError(
                "dataset_id must start with a letter or digit and contain only letters, "
                "digits, '.', '_', ':' or '-'."
            )
        object.__setattr__(self, "dataset_id", dataset_id)

        if isinstance(self.dataset_version, bool) or not isinstance(self.dataset_version, int):
            raise TypeError("dataset_version must be an integer.")
        if self.dataset_version < 1:
            raise CanonicalDatasetReferenceError("dataset_version must be at least 1.")

        runtime_mode = _required("runtime_mode", self.runtime_mode).lower()
        if not _RUNTIME_PATTERN.fullmatch(runtime_mode):
            raise CanonicalDatasetReferenceError(
                "runtime_mode must start with a lowercase letter and contain only "
                "lowercase letters, digits, '_' or '-'."
            )
        object.__setattr__(self, "runtime_mode", runtime_mode)

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")
        normalised: dict[str, object] = {}
        for key, value in self.attributes.items():
            if not isinstance(key, str):
                raise TypeError("attribute keys must be text.")
            key = key.strip()
            if not key:
                raise CanonicalDatasetReferenceError("attribute keys cannot be empty.")
            if key in normalised:
                raise CanonicalDatasetReferenceError(
                    "attribute keys must remain unique after whitespace normalization."
                )
            normalised[key] = _freeze(value)
        object.__setattr__(self, "attributes", MappingProxyType(normalised))

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "runtime_mode": self.runtime_mode,
            "attributes": _thaw(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "CanonicalDatasetReference":
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {"dataset_id", "dataset_version", "runtime_mode", "attributes"}
        unknown = set(data) - allowed
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise CanonicalDatasetReferenceError(f"unknown canonical dataset reference fields: {names}.")
        try:
            return cls(**dict(data))
        except TypeError as exc:
            if "required positional argument" in str(exc):
                raise CanonicalDatasetReferenceError("missing required canonical dataset reference field.") from exc
            raise


__all__ = ["CanonicalDatasetReference", "CanonicalDatasetReferenceError"]
