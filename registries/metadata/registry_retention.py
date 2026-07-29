"""Immutable registry-level retention policy declaration.

The contract declares preservation expectations and future disposition
constraints.  It does not delete records, move archives, release legal holds,
resolve cross-registry dependencies, or calculate jurisdiction-specific law.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from typing import Final

from .registry_metadata_errors import RegistryRetentionError
from .registry_retention_mode import RegistryRetentionMode

_MAX_REASON_LENGTH: Final[int] = 2_000
_MAX_TRIGGER_EVENT_LENGTH: Final[int] = 255
_MAX_POLICY_REFERENCE_LENGTH: Final[int] = 512
_TRIGGER_EVENT_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Z0-9][A-Z0-9_.:-]*$"
)


def _normalise_text(
    value: object,
    name: str,
    *,
    maximum_length: int,
    required: bool = False,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text.")
    normalized = value.strip()
    if required and not normalized:
        raise RegistryRetentionError(f"{name} cannot be empty.")
    if len(normalized) > maximum_length:
        raise RegistryRetentionError(
            f"{name} cannot exceed {maximum_length} characters."
        )
    return normalized


def _normalise_trigger_event(value: object) -> str:
    normalized = _normalise_text(
        value,
        "trigger_event",
        maximum_length=_MAX_TRIGGER_EVENT_LENGTH,
    ).upper()
    if normalized and not _TRIGGER_EVENT_PATTERN.fullmatch(normalized):
        raise RegistryRetentionError(
            "trigger_event must be a semantic code using letters, digits, "
            "underscores, dots, colons or hyphens."
        )
    return normalized


def _normalise_datetime(value: object, name: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime or None.")
    if value.tzinfo is None or value.utcoffset() is None:
        raise RegistryRetentionError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _parse_datetime(value: object, name: str) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return _normalise_datetime(value, name)
    if not isinstance(value, str):
        raise TypeError(
            f"{name} must be an ISO datetime string, datetime or None."
        )
    normalized = value.strip()
    if not normalized:
        raise RegistryRetentionError(
            f"{name} cannot be an empty datetime string."
        )
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RegistryRetentionError(
            f"{name} must be a valid ISO datetime string."
        ) from exc
    return _normalise_datetime(parsed, name)


def _normalise_period(value: object) -> timedelta | None:
    if value is None:
        return None
    if not isinstance(value, timedelta):
        raise TypeError("retention_period must be a timedelta or None.")
    total_seconds = value.total_seconds()
    if total_seconds <= 0:
        raise RegistryRetentionError("retention_period must be positive.")
    if not total_seconds.is_integer():
        raise RegistryRetentionError(
            "retention_period must use whole-second precision."
        )
    return value


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
        return {
            key: _thaw_attribute_value(nested)
            for key, nested in value.items()
        }
    if isinstance(value, tuple):
        return [_thaw_attribute_value(item) for item in value]
    if isinstance(value, frozenset):
        return [
            _thaw_attribute_value(item)
            for item in sorted(value, key=lambda item: repr(item))
        ]
    return value


@dataclass(frozen=True, slots=True)
class RegistryRetention:
    """One immutable and versioned registry retention declaration."""

    mode: RegistryRetentionMode
    reason: str
    retention_period: timedelta | None = None
    retain_until: datetime | None = None
    trigger_event: str = ""
    archive_required: bool = False
    deletion_permitted: bool = False
    legal_hold: bool = False
    review_at: datetime | None = None
    policy_reference: str = ""
    version: int = 1
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        try:
            mode = RegistryRetentionMode.from_value(self.mode)
        except ValueError as exc:
            raise RegistryRetentionError(str(exc)) from exc
        object.__setattr__(self, "mode", mode)

        object.__setattr__(
            self,
            "reason",
            _normalise_text(
                self.reason,
                "reason",
                maximum_length=_MAX_REASON_LENGTH,
                required=True,
            ),
        )
        object.__setattr__(
            self,
            "policy_reference",
            _normalise_text(
                self.policy_reference,
                "policy_reference",
                maximum_length=_MAX_POLICY_REFERENCE_LENGTH,
            ),
        )
        object.__setattr__(
            self,
            "trigger_event",
            _normalise_trigger_event(self.trigger_event),
        )

        for name in ("archive_required", "deletion_permitted", "legal_hold"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean.")

        object.__setattr__(
            self,
            "retention_period",
            _normalise_period(self.retention_period),
        )
        object.__setattr__(
            self,
            "retain_until",
            _normalise_datetime(self.retain_until, "retain_until"),
        )
        object.__setattr__(
            self,
            "review_at",
            _normalise_datetime(self.review_at, "review_at"),
        )

        if self.legal_hold and self.deletion_permitted:
            raise RegistryRetentionError("legal hold cannot permit deletion.")

        if mode is RegistryRetentionMode.PERMANENT:
            if self.deletion_permitted:
                raise RegistryRetentionError(
                    "PERMANENT retention cannot permit deletion."
                )
            if self.retention_period is not None or self.retain_until is not None:
                raise RegistryRetentionError(
                    "PERMANENT retention cannot declare a duration or retain-until date."
                )
            if self.trigger_event:
                raise RegistryRetentionError(
                    "PERMANENT retention cannot declare a trigger event."
                )
            if self.legal_hold:
                raise RegistryRetentionError(
                    "PERMANENT retention cannot also declare legal_hold=True."
                )

        elif mode is RegistryRetentionMode.FIXED_DURATION:
            if self.retention_period is None:
                raise RegistryRetentionError(
                    "FIXED_DURATION requires retention_period."
                )
            if self.retain_until is not None or self.trigger_event:
                raise RegistryRetentionError(
                    "FIXED_DURATION cannot declare retain_until or trigger_event."
                )

        elif mode is RegistryRetentionMode.UNTIL_DATE:
            if self.retain_until is None:
                raise RegistryRetentionError("UNTIL_DATE requires retain_until.")
            if self.retention_period is not None or self.trigger_event:
                raise RegistryRetentionError(
                    "UNTIL_DATE cannot declare retention_period or trigger_event."
                )

        elif mode is RegistryRetentionMode.EVENT_TRIGGERED:
            if not self.trigger_event:
                raise RegistryRetentionError(
                    "EVENT_TRIGGERED requires trigger_event."
                )
            if self.retain_until is not None:
                raise RegistryRetentionError(
                    "EVENT_TRIGGERED cannot declare retain_until."
                )

        elif mode is RegistryRetentionMode.LEGAL_HOLD:
            if not self.legal_hold:
                raise RegistryRetentionError(
                    "LEGAL_HOLD requires legal_hold=True."
                )
            if self.retention_period is not None or self.retain_until is not None:
                raise RegistryRetentionError(
                    "LEGAL_HOLD cannot declare a duration or retain-until date."
                )
            if self.trigger_event:
                raise RegistryRetentionError(
                    "LEGAL_HOLD cannot declare a trigger event."
                )
            if not (self.review_at is not None or self.policy_reference):
                raise RegistryRetentionError(
                    "LEGAL_HOLD requires review_at or policy_reference."
                )

        elif mode is RegistryRetentionMode.POLICY_REVIEW_REQUIRED:
            if self.retention_period is not None or self.retain_until is not None:
                raise RegistryRetentionError(
                    "POLICY_REVIEW_REQUIRED cannot declare a duration or retain-until date."
                )
            if self.trigger_event:
                raise RegistryRetentionError(
                    "POLICY_REVIEW_REQUIRED cannot declare a trigger event."
                )
            if not (self.review_at is not None or self.policy_reference):
                raise RegistryRetentionError(
                    "POLICY_REVIEW_REQUIRED requires review_at or policy_reference."
                )

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < 1:
            raise RegistryRetentionError("version must be at least 1.")

        if not isinstance(self.attributes, Mapping):
            raise TypeError("attributes must be a mapping.")
        normalized_attributes: dict[str, object] = {}
        for key, value in self.attributes.items():
            if not isinstance(key, str):
                raise TypeError("attribute keys must be text.")
            normalized_key = key.strip()
            if not normalized_key:
                raise RegistryRetentionError("attribute keys cannot be empty.")
            if normalized_key in normalized_attributes:
                raise RegistryRetentionError(
                    "attribute keys must remain unique after whitespace normalization."
                )
            normalized_attributes[normalized_key] = _freeze_attribute_value(value)
        object.__setattr__(
            self,
            "attributes",
            MappingProxyType(normalized_attributes),
        )

    def to_dict(self) -> dict[str, object]:
        """Return a deeply detached persistence or transport representation."""
        return {
            "mode": self.mode.value,
            "reason": self.reason,
            "retention_seconds": (
                None
                if self.retention_period is None
                else int(self.retention_period.total_seconds())
            ),
            "retain_until": (
                None if self.retain_until is None else self.retain_until.isoformat()
            ),
            "trigger_event": self.trigger_event,
            "archive_required": self.archive_required,
            "deletion_permitted": self.deletion_permitted,
            "legal_hold": self.legal_hold,
            "review_at": None if self.review_at is None else self.review_at.isoformat(),
            "policy_reference": self.policy_reference,
            "version": self.version,
            "attributes": _thaw_attribute_value(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RegistryRetention":
        """Reconstruct a declaration from a detached persistence mapping."""
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        values = dict(data)
        if "retention_seconds" in values:
            seconds = values.pop("retention_seconds")
            if seconds is None:
                values["retention_period"] = None
            else:
                if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
                    raise TypeError("retention_seconds must be a number or None.")
                if float(seconds) <= 0:
                    raise RegistryRetentionError(
                        "retention_seconds must be positive."
                    )
                if not float(seconds).is_integer():
                    raise RegistryRetentionError(
                        "retention_seconds must use whole-second precision."
                    )
                values["retention_period"] = timedelta(seconds=int(seconds))
        if "retain_until" in values:
            values["retain_until"] = _parse_datetime(
                values["retain_until"],
                "retain_until",
            )
        if "review_at" in values:
            values["review_at"] = _parse_datetime(
                values["review_at"],
                "review_at",
            )
        return cls(**values)


__all__ = ["RegistryRetention"]
