"""Immutable direction contracts for cross-registry relationships.

M008.16.3 declares how one semantic relationship type may be interpreted from
its source and target sides.  It does not persist relationships, resolve
registry records, enforce cardinality, publish events, or apply domain policy.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Final

from .relationship_type import RelationshipType

_DIRECTION_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$"
)
_DIRECTION_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*)+$"
)
_MAX_LABEL_LENGTH: Final[int] = 200


class RelationshipDirectionError(ValueError):
    """Raised when a relationship-direction contract is invalid."""


class RelationshipDirectionMode(str, Enum):
    """Stable direction modes supported by the relationship foundation."""

    FORWARD_ONLY = "forward_only"
    INVERSE = "inverse"
    SYMMETRIC = "symmetric"


@dataclass(frozen=True, slots=True)
class RelationshipDirection:
    """Immutable semantic direction definition for one relationship type."""

    direction_id: str
    direction_code: str
    mode: RelationshipDirectionMode
    forward_type: RelationshipType
    inverse_type: RelationshipType | None = None
    forward_label: str = ""
    reverse_label: str = ""
    version: int = 1

    def __post_init__(self) -> None:
        direction_id = _required("direction_id", self.direction_id)
        if not _DIRECTION_ID_PATTERN.fullmatch(direction_id):
            raise RelationshipDirectionError(
                "direction_id must start with a letter or digit and contain only "
                "letters, digits, '.', '_', ':' or '-'."
            )
        object.__setattr__(self, "direction_id", direction_id)

        direction_code = _required("direction_code", self.direction_code).upper()
        if not _DIRECTION_CODE_PATTERN.fullmatch(direction_code):
            raise RelationshipDirectionError(
                "direction_code must be a hierarchical dotted code with at least "
                "two uppercase semantic segments."
            )
        object.__setattr__(self, "direction_code", direction_code)

        if not isinstance(self.mode, RelationshipDirectionMode):
            raise TypeError("mode must be a RelationshipDirectionMode.")
        if not isinstance(self.forward_type, RelationshipType):
            raise TypeError("forward_type must be a RelationshipType.")
        if self.inverse_type is not None and not isinstance(
            self.inverse_type, RelationshipType
        ):
            raise TypeError("inverse_type must be a RelationshipType or None.")

        forward_label = _optional_label("forward_label", self.forward_label)
        reverse_label = _optional_label("reverse_label", self.reverse_label)
        object.__setattr__(self, "forward_label", forward_label)
        object.__setattr__(self, "reverse_label", reverse_label)

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < 1:
            raise RelationshipDirectionError("version must be at least 1.")

        if self.mode is RelationshipDirectionMode.FORWARD_ONLY:
            if self.inverse_type is not None:
                raise RelationshipDirectionError(
                    "forward-only directions cannot declare an inverse type."
                )
            if self.reverse_label:
                raise RelationshipDirectionError(
                    "forward-only directions cannot declare a reverse label."
                )

        elif self.mode is RelationshipDirectionMode.INVERSE:
            if self.inverse_type is None:
                raise RelationshipDirectionError(
                    "inverse directions must declare an inverse type."
                )
            if _type_identity(self.forward_type) == _type_identity(self.inverse_type):
                raise RelationshipDirectionError(
                    "inverse directions must use distinct forward and inverse types."
                )

        elif self.mode is RelationshipDirectionMode.SYMMETRIC:
            if self.inverse_type is not None and (
                _type_identity(self.inverse_type) != _type_identity(self.forward_type)
            ):
                raise RelationshipDirectionError(
                    "symmetric directions may only repeat the forward type as inverse."
                )
            object.__setattr__(self, "inverse_type", self.forward_type)

    @property
    def allows_reverse(self) -> bool:
        """Return whether the relationship may be interpreted in reverse."""
        return self.mode is not RelationshipDirectionMode.FORWARD_ONLY

    @property
    def preserves_meaning_when_reversed(self) -> bool:
        """Return whether reversal retains the same semantic relationship type."""
        return self.mode is RelationshipDirectionMode.SYMMETRIC

    def type_for_reverse(self) -> RelationshipType | None:
        """Return the explicit reverse semantic type, if reverse use is allowed."""
        return self.inverse_type if self.allows_reverse else None

    def to_dict(self) -> dict[str, object]:
        """Return a detached transport-safe representation."""
        return {
            "direction_id": self.direction_id,
            "direction_code": self.direction_code,
            "mode": self.mode.value,
            "forward_type": self.forward_type.to_dict(),
            "inverse_type": (
                None if self.inverse_type is None else self.inverse_type.to_dict()
            ),
            "forward_label": self.forward_label,
            "reverse_label": self.reverse_label,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RelationshipDirection":
        """Rebuild a direction contract from its serialized representation."""
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {
            "direction_id",
            "direction_code",
            "mode",
            "forward_type",
            "inverse_type",
            "forward_label",
            "reverse_label",
            "version",
        }
        unknown = set(data) - allowed
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise RelationshipDirectionError(
                f"unknown relationship direction fields: {names}."
            )
        payload = dict(data)
        try:
            if not isinstance(payload["mode"], RelationshipDirectionMode):
                payload["mode"] = RelationshipDirectionMode(payload["mode"])
            if not isinstance(payload["forward_type"], RelationshipType):
                payload["forward_type"] = RelationshipType.from_dict(
                    payload["forward_type"]
                )
            inverse = payload.get("inverse_type")
            if inverse is not None and not isinstance(inverse, RelationshipType):
                payload["inverse_type"] = RelationshipType.from_dict(inverse)
        except KeyError as exc:
            raise RelationshipDirectionError(
                f"missing required relationship direction field: {exc.args[0]}."
            ) from exc
        except ValueError as exc:
            if isinstance(exc, RelationshipDirectionError):
                raise
            raise RelationshipDirectionError("unknown relationship direction mode.") from exc
        return cls(**payload)


def _required(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text.")
    normalised = value.strip()
    if not normalised:
        raise RelationshipDirectionError(f"{name} cannot be empty.")
    return normalised


def _optional_label(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be text.")
    normalised = value.strip()
    if len(normalised) > _MAX_LABEL_LENGTH:
        raise RelationshipDirectionError(
            f"{name} cannot exceed {_MAX_LABEL_LENGTH} characters."
        )
    return normalised


def _type_identity(relationship_type: RelationshipType) -> tuple[str, str, int]:
    return (
        relationship_type.relationship_type_id,
        relationship_type.relationship_type_code,
        relationship_type.version,
    )


__all__ = [
    "RelationshipDirection",
    "RelationshipDirectionError",
    "RelationshipDirectionMode",
]
