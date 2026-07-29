"""Immutable result contracts for cross-registry reference comparisons.

These value objects report whether a proposed reference or relationship keeps
all identity-bearing fields unchanged.  They do not resolve registry records,
persist relationships, publish events, or decide domain-specific corrections.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Final


class ImmutableReferenceField(str, Enum):
    """Identity-bearing fields protected by M008.16.2 rules."""

    REGISTRY_ID = "registry_id"
    RECORD_ID = "record_id"
    REFERENCE_VERSION = "reference_version"
    RELATIONSHIP_ID = "relationship_id"
    RELATIONSHIP_TYPE_ID = "relationship_type_id"
    RELATIONSHIP_TYPE_CODE = "relationship_type_code"
    SOURCE_REGISTRY_ID = "source.registry_id"
    SOURCE_RECORD_ID = "source.record_id"
    SOURCE_VERSION = "source.version"
    TARGET_REGISTRY_ID = "target.registry_id"
    TARGET_RECORD_ID = "target.record_id"
    TARGET_VERSION = "target.version"
    RUNTIME_MODE = "runtime_mode"
    RELATIONSHIP_VERSION = "relationship_version"


class ImmutableReferenceViolationCode(str, Enum):
    """Stable machine-readable reason codes for rejected replacements."""

    REGISTRY_ID_CHANGED = "REGISTRY_ID_CHANGED"
    RECORD_ID_CHANGED = "RECORD_ID_CHANGED"
    REFERENCE_VERSION_CHANGED = "REFERENCE_VERSION_CHANGED"
    RELATIONSHIP_ID_CHANGED = "RELATIONSHIP_ID_CHANGED"
    RELATIONSHIP_TYPE_ID_CHANGED = "RELATIONSHIP_TYPE_ID_CHANGED"
    RELATIONSHIP_TYPE_CODE_CHANGED = "RELATIONSHIP_TYPE_CODE_CHANGED"
    SOURCE_REGISTRY_ID_CHANGED = "SOURCE_REGISTRY_ID_CHANGED"
    SOURCE_RECORD_ID_CHANGED = "SOURCE_RECORD_ID_CHANGED"
    SOURCE_VERSION_CHANGED = "SOURCE_VERSION_CHANGED"
    TARGET_REGISTRY_ID_CHANGED = "TARGET_REGISTRY_ID_CHANGED"
    TARGET_RECORD_ID_CHANGED = "TARGET_RECORD_ID_CHANGED"
    TARGET_VERSION_CHANGED = "TARGET_VERSION_CHANGED"
    RUNTIME_MODE_CHANGED = "RUNTIME_MODE_CHANGED"
    RELATIONSHIP_VERSION_CHANGED = "RELATIONSHIP_VERSION_CHANGED"


@dataclass(frozen=True, slots=True)
class ImmutableReferenceFinding:
    """One deterministic immutable-field difference."""

    code: ImmutableReferenceViolationCode
    field: ImmutableReferenceField
    existing_value: object
    proposed_value: object

    def __post_init__(self) -> None:
        if not isinstance(self.code, ImmutableReferenceViolationCode):
            raise TypeError("code must be an ImmutableReferenceViolationCode.")
        if not isinstance(self.field, ImmutableReferenceField):
            raise TypeError("field must be an ImmutableReferenceField.")

    def to_dict(self) -> dict[str, object]:
        """Return a detached, transport-safe representation."""
        return {
            "code": self.code.value,
            "field": self.field.value,
            "existing_value": self.existing_value,
            "proposed_value": self.proposed_value,
        }


_FINDING_ORDER: Final[dict[ImmutableReferenceField, int]] = {
    field: index for index, field in enumerate(ImmutableReferenceField)
}


@dataclass(frozen=True, slots=True)
class ImmutableReferenceResult:
    """Complete deterministic outcome of one immutable-reference comparison."""

    findings: tuple[ImmutableReferenceFinding, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple.")
        for finding in self.findings:
            if not isinstance(finding, ImmutableReferenceFinding):
                raise TypeError("findings must contain ImmutableReferenceFinding values.")
        ordered = tuple(
            sorted(
                self.findings,
                key=lambda finding: (
                    _FINDING_ORDER[finding.field],
                    finding.code.value,
                ),
            )
        )
        fields = [finding.field for finding in ordered]
        if len(fields) != len(set(fields)):
            raise ValueError("findings must contain at most one result per immutable field.")
        object.__setattr__(self, "findings", ordered)

    @property
    def is_compatible(self) -> bool:
        """Return True when no immutable identity field changed."""
        return not self.findings

    @property
    def changed_fields(self) -> tuple[ImmutableReferenceField, ...]:
        """Return changed fields in stable contract order."""
        return tuple(finding.field for finding in self.findings)

    @property
    def violations(self) -> tuple[ImmutableReferenceViolationCode, ...]:
        """Return violation codes in stable contract order."""
        return tuple(finding.code for finding in self.findings)

    def to_dict(self) -> dict[str, object]:
        """Return a detached representation suitable for APIs and audits."""
        return {
            "is_compatible": self.is_compatible,
            "changed_fields": [field.value for field in self.changed_fields],
            "violations": [code.value for code in self.violations],
            "findings": [finding.to_dict() for finding in self.findings],
        }

    @classmethod
    def compatible(cls) -> "ImmutableReferenceResult":
        """Construct the canonical compatible result."""
        return cls()

    @classmethod
    def from_findings(
        cls, findings: Iterable[ImmutableReferenceFinding]
    ) -> "ImmutableReferenceResult":
        """Construct from any finite iterable without retaining caller storage."""
        if isinstance(findings, (str, bytes, Mapping)):
            raise TypeError("findings must be an iterable of findings.")
        try:
            detached = tuple(findings)
        except TypeError as exc:
            raise TypeError("findings must be an iterable of findings.") from exc
        return cls(detached)

    def findings_by_field(
        self,
    ) -> Mapping[ImmutableReferenceField, ImmutableReferenceFinding]:
        """Return a read-only field-indexed view of the findings."""
        return MappingProxyType({finding.field: finding for finding in self.findings})


__all__ = [
    "ImmutableReferenceField",
    "ImmutableReferenceFinding",
    "ImmutableReferenceResult",
    "ImmutableReferenceViolationCode",
]
