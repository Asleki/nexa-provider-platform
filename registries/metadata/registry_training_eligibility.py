"""Immutable registry-level AI training eligibility declaration.

The contract declares whether registry data may be considered for a future
training or evaluation purpose.  It does not train a model, build a dataset,
verify consent, perform anonymisation, interpret evidence quality, or approve
model deployment.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from .registry_metadata_errors import RegistryTrainingEligibilityError
from .registry_training_eligibility_status import RegistryTrainingEligibilityStatus

_MAX_REASON_LENGTH: Final[int] = 2_000
_MAX_PURPOSE_CODE_LENGTH: Final[int] = 255
_PURPOSE_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*$"
)


def _freeze_attribute_value(value: object) -> object:
    """Return an immutable snapshot of a nested extension value."""
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
    """Return a deeply detached persistence-style representation."""
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


def _normalise_purpose_restrictions(value: object) -> tuple[str, ...]:
    """Validate and canonicalise open semantic training-purpose codes."""
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise TypeError("purpose_restrictions must be an iterable of text values.")

    restrictions: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise TypeError("purpose_restrictions must contain text values.")
        normalized = item.strip().lower()
        if not normalized:
            raise RegistryTrainingEligibilityError(
                "purpose restrictions cannot be empty."
            )
        if len(normalized) > _MAX_PURPOSE_CODE_LENGTH:
            raise RegistryTrainingEligibilityError(
                "purpose restriction codes cannot exceed "
                f"{_MAX_PURPOSE_CODE_LENGTH} characters."
            )
        if not _PURPOSE_CODE_PATTERN.fullmatch(normalized):
            raise RegistryTrainingEligibilityError(
                "purpose restriction codes must be lowercase semantic codes "
                "using letters, digits, underscores and optional dotted segments."
            )
        if normalized not in seen:
            seen.add(normalized)
            restrictions.append(normalized)
    return tuple(restrictions)


@dataclass(frozen=True, slots=True)
class RegistryTrainingEligibility:
    """One immutable, versioned training-eligibility declaration."""

    status: RegistryTrainingEligibilityStatus
    reason: str
    anonymisation_required: bool = False
    aggregation_required: bool = False
    human_approval_required: bool = False
    consent_required: bool = False
    simulation_only: bool = False
    purpose_restrictions: tuple[str, ...] = field(default_factory=tuple)
    version: int = 1
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        try:
            status = RegistryTrainingEligibilityStatus.from_value(self.status)
        except ValueError as exc:
            raise RegistryTrainingEligibilityError(str(exc)) from exc
        object.__setattr__(self, "status", status)

        if not isinstance(self.reason, str):
            raise TypeError("reason must be text.")
        reason = self.reason.strip()
        if not reason:
            raise RegistryTrainingEligibilityError("reason cannot be empty.")
        if len(reason) > _MAX_REASON_LENGTH:
            raise RegistryTrainingEligibilityError(
                f"reason cannot exceed {_MAX_REASON_LENGTH} characters."
            )
        object.__setattr__(self, "reason", reason)

        condition_flags = (
            "anonymisation_required",
            "aggregation_required",
            "human_approval_required",
            "consent_required",
            "simulation_only",
        )
        for name in condition_flags:
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean.")

        restrictions = _normalise_purpose_restrictions(self.purpose_restrictions)
        object.__setattr__(self, "purpose_restrictions", restrictions)

        processing_conditions = (
            self.anonymisation_required,
            self.aggregation_required,
            self.human_approval_required,
            self.consent_required,
            bool(self.purpose_restrictions),
        )
        any_processing_condition = any(processing_conditions)
        any_condition = any_processing_condition or self.simulation_only

        if self.status is RegistryTrainingEligibilityStatus.ELIGIBLE:
            if any_processing_condition:
                raise RegistryTrainingEligibilityError(
                    "ELIGIBLE status cannot declare processing or approval conditions."
                )
        elif self.status is RegistryTrainingEligibilityStatus.CONDITIONALLY_ELIGIBLE:
            if not any_condition:
                raise RegistryTrainingEligibilityError(
                    "CONDITIONALLY_ELIGIBLE status must declare at least one condition."
                )
        elif self.status in (
            RegistryTrainingEligibilityStatus.INELIGIBLE,
            RegistryTrainingEligibilityStatus.PROHIBITED,
            RegistryTrainingEligibilityStatus.UNREVIEWED,
        ):
            if any_condition:
                raise RegistryTrainingEligibilityError(
                    f"{self.status.name} status cannot declare eligibility conditions."
                )

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < 1:
            raise RegistryTrainingEligibilityError("version must be at least 1.")

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")
        normalized_attributes: dict[str, object] = {}
        for key, value in self.attributes.items():
            if not isinstance(key, str):
                raise TypeError("attribute keys must be text.")
            normalized_key = key.strip()
            if not normalized_key:
                raise RegistryTrainingEligibilityError(
                    "attribute keys cannot be empty."
                )
            if normalized_key in normalized_attributes:
                raise RegistryTrainingEligibilityError(
                    "attribute keys must remain unique after whitespace normalization."
                )
            normalized_attributes[normalized_key] = _freeze_attribute_value(value)
        object.__setattr__(
            self,
            "attributes",
            MappingProxyType(normalized_attributes),
        )

    @property
    def may_be_considered(self) -> bool:
        """Whether later governance may consider this data for a permitted purpose."""
        return self.status in (
            RegistryTrainingEligibilityStatus.ELIGIBLE,
            RegistryTrainingEligibilityStatus.CONDITIONALLY_ELIGIBLE,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deeply detached representation for persistence or transport."""
        return {
            "status": self.status.value,
            "reason": self.reason,
            "anonymisation_required": self.anonymisation_required,
            "aggregation_required": self.aggregation_required,
            "human_approval_required": self.human_approval_required,
            "consent_required": self.consent_required,
            "simulation_only": self.simulation_only,
            "purpose_restrictions": list(self.purpose_restrictions),
            "version": self.version,
            "attributes": _thaw_attribute_value(self.attributes),
        }

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, object],
    ) -> "RegistryTrainingEligibility":
        """Build a declaration from a mapping without retaining caller ownership."""
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        return cls(**dict(data))


__all__ = ["RegistryTrainingEligibility"]
