"""Structural constraint evaluation for cross-registry relationships.

The evaluator consumes one immutable relationship, one immutable constraint and
caller-supplied existing counts.  It does not query storage, resolve endpoint
records, inspect lifecycle state, traverse graphs, alter relationships, or apply
domain-specific eligibility policy.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from .constraint_contract import (
    RelationshipConstraint,
    RelationshipDuplicatePolicy,
    RelationshipSelfReferencePolicy,
)
from .relationship_definition import RelationshipDefinition
from .relationship_type import RelationshipType


class RelationshipConstraintViolationCode(str, Enum):
    """Stable machine-readable structural rejection reasons."""

    RELATIONSHIP_TYPE_MISMATCH = "RELATIONSHIP_TYPE_MISMATCH"
    RUNTIME_MODE_NOT_ALLOWED = "RUNTIME_MODE_NOT_ALLOWED"
    SOURCE_REGISTRY_NOT_ALLOWED = "SOURCE_REGISTRY_NOT_ALLOWED"
    TARGET_REGISTRY_NOT_ALLOWED = "TARGET_REGISTRY_NOT_ALLOWED"
    SELF_REFERENCE_PROHIBITED = "SELF_REFERENCE_PROHIBITED"
    DUPLICATE_PAIR_PROHIBITED = "DUPLICATE_PAIR_PROHIBITED"
    SOURCE_CARDINALITY_EXCEEDED = "SOURCE_CARDINALITY_EXCEEDED"
    TARGET_CARDINALITY_EXCEEDED = "TARGET_CARDINALITY_EXCEEDED"


@dataclass(frozen=True, slots=True)
class RelationshipConstraintContext:
    """Existing repository facts supplied before adding the candidate link."""

    existing_source_count: int = 0
    existing_target_count: int = 0
    existing_pair_count: int = 0

    def __post_init__(self) -> None:
        _validate_count("existing_source_count", self.existing_source_count)
        _validate_count("existing_target_count", self.existing_target_count)
        _validate_count("existing_pair_count", self.existing_pair_count)

    def to_dict(self) -> dict[str, int]:
        return {
            "existing_source_count": self.existing_source_count,
            "existing_target_count": self.existing_target_count,
            "existing_pair_count": self.existing_pair_count,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "RelationshipConstraintContext":
        if not isinstance(data, Mapping):
            raise TypeError("data must be a mapping.")
        allowed = {
            "existing_source_count",
            "existing_target_count",
            "existing_pair_count",
        }
        unknown = set(data) - allowed
        if unknown:
            names = ", ".join(sorted(str(name) for name in unknown))
            raise RelationshipConstraintRuleError(
                f"unknown relationship constraint context fields: {names}."
            )
        return cls(**dict(data))


@dataclass(frozen=True, slots=True)
class RelationshipConstraintFinding:
    """One deterministic structural constraint violation."""

    code: RelationshipConstraintViolationCode
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, RelationshipConstraintViolationCode):
            raise TypeError("code must be a RelationshipConstraintViolationCode.")
        if not isinstance(self.message, str):
            raise TypeError("message must be text.")
        message = self.message.strip()
        if not message:
            raise ValueError("message cannot be empty.")
        object.__setattr__(self, "message", message)

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code.value, "message": self.message}


@dataclass(frozen=True, slots=True)
class RelationshipConstraintResult:
    """Deterministic result of evaluating one proposed relationship."""

    findings: tuple[RelationshipConstraintFinding, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple.")
        seen: set[RelationshipConstraintViolationCode] = set()
        for finding in self.findings:
            if not isinstance(finding, RelationshipConstraintFinding):
                raise TypeError(
                    "findings must contain RelationshipConstraintFinding values."
                )
            if finding.code in seen:
                raise ValueError("finding codes must be unique.")
            seen.add(finding.code)

    @property
    def is_compatible(self) -> bool:
        return not self.findings

    @property
    def violations(self) -> tuple[RelationshipConstraintViolationCode, ...]:
        return tuple(finding.code for finding in self.findings)

    @classmethod
    def compatible(cls) -> "RelationshipConstraintResult":
        return cls()

    @classmethod
    def from_findings(
        cls, *findings: RelationshipConstraintFinding
    ) -> "RelationshipConstraintResult":
        return cls(tuple(findings))

    def to_dict(self) -> dict[str, object]:
        return {
            "is_compatible": self.is_compatible,
            "violations": [code.value for code in self.violations],
            "findings": [finding.to_dict() for finding in self.findings],
        }


class RelationshipConstraintRuleError(ValueError):
    """Base error for invalid constraint-rule operations."""


class RelationshipConstraintViolation(RelationshipConstraintRuleError):
    """Raised when a proposed relationship violates structural policy."""

    def __init__(self, result: RelationshipConstraintResult) -> None:
        if not isinstance(result, RelationshipConstraintResult):
            raise TypeError("result must be a RelationshipConstraintResult.")
        if result.is_compatible:
            raise ValueError("a compatible result cannot raise a constraint violation.")
        self.result = result
        codes = ", ".join(code.value for code in result.violations)
        super().__init__(f"relationship constraints violated: {codes}.")


def evaluate_relationship_constraints(
    relationship: RelationshipDefinition,
    constraint: RelationshipConstraint,
    context: RelationshipConstraintContext | None = None,
) -> RelationshipConstraintResult:
    """Evaluate a relationship using supplied pre-insertion repository facts."""
    if not isinstance(relationship, RelationshipDefinition):
        raise TypeError("relationship must be a RelationshipDefinition.")
    if not isinstance(constraint, RelationshipConstraint):
        raise TypeError("constraint must be a RelationshipConstraint.")
    if context is None:
        context = RelationshipConstraintContext()
    if not isinstance(context, RelationshipConstraintContext):
        raise TypeError("context must be a RelationshipConstraintContext or None.")

    findings: list[RelationshipConstraintFinding] = []

    if _type_identity(relationship.relationship_type) != _type_identity(
        constraint.relationship_type
    ):
        findings.append(
            RelationshipConstraintFinding(
                RelationshipConstraintViolationCode.RELATIONSHIP_TYPE_MISMATCH,
                "relationship type does not match the constraint relationship type.",
            )
        )

    if not constraint.applies_to_runtime(relationship.runtime_mode):
        findings.append(
            RelationshipConstraintFinding(
                RelationshipConstraintViolationCode.RUNTIME_MODE_NOT_ALLOWED,
                f"runtime mode '{relationship.runtime_mode}' is not allowed by the constraint.",
            )
        )

    if not constraint.allows_source_registry(relationship.source.registry_id):
        findings.append(
            RelationshipConstraintFinding(
                RelationshipConstraintViolationCode.SOURCE_REGISTRY_NOT_ALLOWED,
                f"source registry '{relationship.source.registry_id}' is not allowed.",
            )
        )

    if not constraint.allows_target_registry(relationship.target.registry_id):
        findings.append(
            RelationshipConstraintFinding(
                RelationshipConstraintViolationCode.TARGET_REGISTRY_NOT_ALLOWED,
                f"target registry '{relationship.target.registry_id}' is not allowed.",
            )
        )

    if (
        constraint.self_reference_policy
        is RelationshipSelfReferencePolicy.PROHIBIT
        and _reference_identity(relationship.source)
        == _reference_identity(relationship.target)
    ):
        findings.append(
            RelationshipConstraintFinding(
                RelationshipConstraintViolationCode.SELF_REFERENCE_PROHIBITED,
                "the same registry record cannot occupy both relationship endpoints.",
            )
        )

    if (
        constraint.duplicate_policy is RelationshipDuplicatePolicy.PROHIBIT
        and context.existing_pair_count > 0
    ):
        findings.append(
            RelationshipConstraintFinding(
                RelationshipConstraintViolationCode.DUPLICATE_PAIR_PROHIBITED,
                "an identical typed source-target pair already exists.",
            )
        )

    proposed_source_count = context.existing_source_count + 1
    source_maximum = constraint.source_cardinality.maximum
    if source_maximum is not None and proposed_source_count > source_maximum:
        findings.append(
            RelationshipConstraintFinding(
                RelationshipConstraintViolationCode.SOURCE_CARDINALITY_EXCEEDED,
                f"proposed source relationship count {proposed_source_count} exceeds maximum {source_maximum}.",
            )
        )

    proposed_target_count = context.existing_target_count + 1
    target_maximum = constraint.target_cardinality.maximum
    if target_maximum is not None and proposed_target_count > target_maximum:
        findings.append(
            RelationshipConstraintFinding(
                RelationshipConstraintViolationCode.TARGET_CARDINALITY_EXCEEDED,
                f"proposed target relationship count {proposed_target_count} exceeds maximum {target_maximum}.",
            )
        )

    return RelationshipConstraintResult(tuple(findings))


def assert_relationship_constraints(
    relationship: RelationshipDefinition,
    constraint: RelationshipConstraint,
    context: RelationshipConstraintContext | None = None,
) -> None:
    """Raise a structured violation when the candidate is incompatible."""
    result = evaluate_relationship_constraints(relationship, constraint, context)
    if not result.is_compatible:
        raise RelationshipConstraintViolation(result)


def _validate_count(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer.")
    if value < 0:
        raise RelationshipConstraintRuleError(f"{name} cannot be negative.")


def _type_identity(relationship_type: RelationshipType) -> tuple[str, str, int]:
    return (
        relationship_type.relationship_type_id,
        relationship_type.relationship_type_code,
        relationship_type.version,
    )


def _reference_identity(reference: object) -> tuple[str, str, int]:
    return (reference.registry_id, reference.record_id, reference.version)


__all__ = [
    "RelationshipConstraintContext",
    "RelationshipConstraintFinding",
    "RelationshipConstraintResult",
    "RelationshipConstraintRuleError",
    "RelationshipConstraintViolation",
    "RelationshipConstraintViolationCode",
    "assert_relationship_constraints",
    "evaluate_relationship_constraints",
]
