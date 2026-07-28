"""Immutable registry-level data classification declaration.

The contract describes sensitivity and information categories.  It does not
perform permission checks, masking, encryption, retention, training approval,
or any other policy-enforcement behaviour.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from .registry_classification_level import RegistryClassificationLevel
from .registry_metadata_errors import RegistryClassificationError

_MAX_REASON_LENGTH: Final[int] = 2_000
_MAX_CATEGORY_CODE_LENGTH: Final[int] = 255
_DATA_CATEGORY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*)+$"
)


def _freeze_attribute_value(value: object) -> object:
    """Return an immutable snapshot of a nested attribute value."""
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
    """Return a detached persistence-style copy of a nested attribute value."""
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


def _normalise_data_categories(value: object) -> tuple[str, ...]:
    """Validate and normalize semantic data-category codes."""
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError("data_categories must be an iterable of text codes.")

    normalized_codes: list[str] = []
    seen: set[str] = set()
    for category in value:
        if not isinstance(category, str):
            raise TypeError("data category codes must be text.")
        normalized = category.strip().upper()
        if not normalized:
            raise RegistryClassificationError("data category codes cannot be empty.")
        if len(normalized) > _MAX_CATEGORY_CODE_LENGTH:
            raise RegistryClassificationError(
                f"data category codes cannot exceed {_MAX_CATEGORY_CODE_LENGTH} characters."
            )
        if not _DATA_CATEGORY_PATTERN.fullmatch(normalized):
            raise RegistryClassificationError(
                "data category codes must be hierarchical dotted codes with at "
                "least two uppercase semantic segments."
            )
        if normalized in seen:
            raise RegistryClassificationError(
                "data category codes must remain unique after normalization."
            )
        seen.add(normalized)
        normalized_codes.append(normalized)
    return tuple(normalized_codes)


@dataclass(frozen=True, slots=True)
class RegistryDataClassification:
    """One immutable, versioned registry data-classification declaration."""

    level: RegistryClassificationLevel
    reason: str
    contains_personal_data: bool = False
    contains_sensitive_personal_data: bool = False
    contains_financial_data: bool = False
    contains_health_data: bool = False
    contains_minor_data: bool = False
    public_disclosure_allowed: bool = False
    masking_required: bool = False
    version: int = 1
    data_categories: tuple[str, ...] = ()
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        try:
            level = RegistryClassificationLevel.from_value(self.level)
        except ValueError as exc:
            raise RegistryClassificationError(str(exc)) from exc
        object.__setattr__(self, "level", level)

        if not isinstance(self.reason, str):
            raise TypeError("reason must be text.")
        reason = self.reason.strip()
        if not reason:
            raise RegistryClassificationError("reason cannot be empty.")
        if len(reason) > _MAX_REASON_LENGTH:
            raise RegistryClassificationError(
                f"reason cannot exceed {_MAX_REASON_LENGTH} characters."
            )
        object.__setattr__(self, "reason", reason)

        flags = (
            "contains_personal_data",
            "contains_sensitive_personal_data",
            "contains_financial_data",
            "contains_health_data",
            "contains_minor_data",
            "public_disclosure_allowed",
            "masking_required",
        )
        for name in flags:
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean.")

        if self.contains_sensitive_personal_data and not self.contains_personal_data:
            raise RegistryClassificationError(
                "sensitive personal data requires contains_personal_data=True."
            )
        if (
            self.level >= RegistryClassificationLevel.CONFIDENTIAL
            and self.public_disclosure_allowed
        ):
            raise RegistryClassificationError(
                "confidential or stronger data cannot allow public disclosure."
            )
        if self.level is RegistryClassificationLevel.PUBLIC and self.masking_required:
            raise RegistryClassificationError(
                "public classification cannot require masking."
            )

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < 1:
            raise RegistryClassificationError("version must be at least 1.")

        object.__setattr__(
            self,
            "data_categories",
            _normalise_data_categories(self.data_categories),
        )

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")
        for key in self.attributes:
            if not isinstance(key, str):
                raise TypeError("attribute keys must be text.")
            if not key.strip():
                raise RegistryClassificationError("attribute keys cannot be empty.")
        frozen_attributes = {
            key.strip(): _freeze_attribute_value(value)
            for key, value in self.attributes.items()
        }
        if len(frozen_attributes) != len(self.attributes):
            raise RegistryClassificationError(
                "attribute keys must remain unique after whitespace normalization."
            )
        object.__setattr__(self, "attributes", MappingProxyType(frozen_attributes))

    def to_dict(self) -> dict[str, object]:
        """Return a deeply detached representation for persistence or transport."""
        return {
            "level": self.level.code,
            "reason": self.reason,
            "contains_personal_data": self.contains_personal_data,
            "contains_sensitive_personal_data": self.contains_sensitive_personal_data,
            "contains_financial_data": self.contains_financial_data,
            "contains_health_data": self.contains_health_data,
            "contains_minor_data": self.contains_minor_data,
            "public_disclosure_allowed": self.public_disclosure_allowed,
            "masking_required": self.masking_required,
            "version": self.version,
            "data_categories": list(self.data_categories),
            "attributes": _thaw_attribute_value(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RegistryDataClassification":
        """Build a declaration from a mapping without retaining caller ownership."""
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        return cls(**dict(data))


__all__ = ["RegistryDataClassification"]
