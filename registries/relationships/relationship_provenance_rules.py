"""Compatibility rules for relationship provenance.

These rules compare one immutable provenance declaration with one immutable
relationship definition. They do not persist, verify, publish, repair, or infer
provenance.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from .provenance_contract import RelationshipProvenance
from .relationship_definition import RelationshipDefinition


class RelationshipProvenanceViolationCode(str, Enum):
    RELATIONSHIP_ID_MISMATCH = "RELATIONSHIP_ID_MISMATCH"
    RELATIONSHIP_VERSION_MISMATCH = "RELATIONSHIP_VERSION_MISMATCH"
    RUNTIME_MODE_MISMATCH = "RUNTIME_MODE_MISMATCH"


@dataclass(frozen=True, slots=True)
class RelationshipProvenanceFinding:
    code: RelationshipProvenanceViolationCode
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, RelationshipProvenanceViolationCode):
            raise TypeError("code must be a RelationshipProvenanceViolationCode.")
        if not isinstance(self.message, str):
            raise TypeError("message must be text.")
        message = self.message.strip()
        if not message:
            raise ValueError("message cannot be empty.")
        object.__setattr__(self, "message", message)

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code.value, "message": self.message}


@dataclass(frozen=True, slots=True)
class RelationshipProvenanceResult:
    findings: tuple[RelationshipProvenanceFinding, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple.")
        seen: set[RelationshipProvenanceViolationCode] = set()
        for finding in self.findings:
            if not isinstance(finding, RelationshipProvenanceFinding):
                raise TypeError("findings must contain RelationshipProvenanceFinding values.")
            if finding.code in seen:
                raise ValueError("finding codes must be unique.")
            seen.add(finding.code)

    @property
    def is_compatible(self) -> bool:
        return not self.findings

    @property
    def violations(self) -> tuple[RelationshipProvenanceViolationCode, ...]:
        return tuple(finding.code for finding in self.findings)

    @classmethod
    def compatible(cls) -> "RelationshipProvenanceResult":
        return cls()

    @classmethod
    def from_findings(
        cls, *findings: RelationshipProvenanceFinding
    ) -> "RelationshipProvenanceResult":
        return cls(tuple(findings))

    def to_dict(self) -> dict[str, object]:
        return {
            "is_compatible": self.is_compatible,
            "violations": [code.value for code in self.violations],
            "findings": [finding.to_dict() for finding in self.findings],
        }


class RelationshipProvenanceRuleError(ValueError):
    """Base error for invalid provenance-rule operations."""


class RelationshipProvenanceViolation(RelationshipProvenanceRuleError):
    """Raised when provenance is incompatible with its relationship."""

    def __init__(self, result: RelationshipProvenanceResult) -> None:
        if not isinstance(result, RelationshipProvenanceResult):
            raise TypeError("result must be a RelationshipProvenanceResult.")
        if result.is_compatible:
            raise ValueError("a compatible result cannot raise a provenance violation.")
        self.result = result
        codes = ", ".join(code.value for code in result.violations)
        super().__init__(f"relationship provenance violated: {codes}.")


def evaluate_relationship_provenance(
    relationship: RelationshipDefinition,
    provenance: RelationshipProvenance,
) -> RelationshipProvenanceResult:
    """Compare immutable relationship identity with immutable provenance."""
    if not isinstance(relationship, RelationshipDefinition):
        raise TypeError("relationship must be a RelationshipDefinition.")
    if not isinstance(provenance, RelationshipProvenance):
        raise TypeError("provenance must be a RelationshipProvenance.")

    findings: list[RelationshipProvenanceFinding] = []

    if provenance.relationship_id != relationship.relationship_id:
        findings.append(
            RelationshipProvenanceFinding(
                RelationshipProvenanceViolationCode.RELATIONSHIP_ID_MISMATCH,
                "provenance relationship_id does not match the relationship identity.",
            )
        )

    if provenance.relationship_version != relationship.version:
        findings.append(
            RelationshipProvenanceFinding(
                RelationshipProvenanceViolationCode.RELATIONSHIP_VERSION_MISMATCH,
                "provenance relationship_version does not match the relationship version.",
            )
        )

    if provenance.runtime_mode != relationship.runtime_mode:
        findings.append(
            RelationshipProvenanceFinding(
                RelationshipProvenanceViolationCode.RUNTIME_MODE_MISMATCH,
                "provenance runtime_mode does not match the relationship runtime mode.",
            )
        )

    return RelationshipProvenanceResult(tuple(findings))


def assert_relationship_provenance(
    relationship: RelationshipDefinition,
    provenance: RelationshipProvenance,
) -> None:
    """Raise a structured violation when provenance is incompatible."""
    result = evaluate_relationship_provenance(relationship, provenance)
    if not result.is_compatible:
        raise RelationshipProvenanceViolation(result)


__all__ = [
    "RelationshipProvenanceFinding",
    "RelationshipProvenanceResult",
    "RelationshipProvenanceRuleError",
    "RelationshipProvenanceViolation",
    "RelationshipProvenanceViolationCode",
    "assert_relationship_provenance",
    "evaluate_relationship_provenance",
]
