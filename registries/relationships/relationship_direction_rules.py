"""Direction evaluation rules for cross-registry relationship definitions.

The rules compare an accepted relationship orientation with a candidate view
using an explicit :class:`RelationshipDirection` contract.  They remain
storage-neutral and do not resolve records, create reverse relationships,
enforce cardinality, or apply domain consequences.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .registry_reference import RegistryReference
from .relationship_definition import RelationshipDefinition
from .direction_contract import RelationshipDirection
from .relationship_type import RelationshipType


class RelationshipOrientation(str, Enum):
    """Observed orientation of a candidate relationship view."""

    FORWARD = "forward"
    REVERSE = "reverse"
    INVALID = "invalid"


class RelationshipDirectionViolationCode(str, Enum):
    """Stable machine-readable direction rejection reasons."""

    RUNTIME_MODE_MISMATCH = "RUNTIME_MODE_MISMATCH"
    ENDPOINT_ORIENTATION_MISMATCH = "ENDPOINT_ORIENTATION_MISMATCH"
    RELATIONSHIP_TYPE_MISMATCH = "RELATIONSHIP_TYPE_MISMATCH"
    REVERSE_NOT_ALLOWED = "REVERSE_NOT_ALLOWED"


@dataclass(frozen=True, slots=True)
class RelationshipDirectionFinding:
    """One deterministic reason a candidate direction is invalid."""

    code: RelationshipDirectionViolationCode
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.code, RelationshipDirectionViolationCode):
            raise TypeError("code must be a RelationshipDirectionViolationCode.")
        if not isinstance(self.message, str):
            raise TypeError("message must be text.")
        message = self.message.strip()
        if not message:
            raise ValueError("message cannot be empty.")
        object.__setattr__(self, "message", message)

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code.value, "message": self.message}


_FINDING_ORDER = {
    code: index for index, code in enumerate(RelationshipDirectionViolationCode)
}


@dataclass(frozen=True, slots=True)
class RelationshipDirectionResult:
    """Deterministic result of evaluating one candidate orientation."""

    orientation: RelationshipOrientation
    findings: tuple[RelationshipDirectionFinding, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.orientation, RelationshipOrientation):
            raise TypeError("orientation must be a RelationshipOrientation.")
        if not isinstance(self.findings, tuple):
            raise TypeError("findings must be a tuple.")
        for finding in self.findings:
            if not isinstance(finding, RelationshipDirectionFinding):
                raise TypeError(
                    "findings must contain RelationshipDirectionFinding values."
                )
        ordered = tuple(
            sorted(
                self.findings,
                key=lambda finding: (_FINDING_ORDER[finding.code], finding.message),
            )
        )
        codes = [finding.code for finding in ordered]
        if len(codes) != len(set(codes)):
            raise ValueError("findings must contain at most one result per code.")
        if self.orientation is RelationshipOrientation.INVALID and not ordered:
            raise ValueError("invalid direction results must contain findings.")
        if self.orientation is not RelationshipOrientation.INVALID and ordered:
            raise ValueError("valid direction results cannot contain findings.")
        object.__setattr__(self, "findings", ordered)

    @property
    def is_valid(self) -> bool:
        return self.orientation is not RelationshipOrientation.INVALID

    @property
    def violations(self) -> tuple[RelationshipDirectionViolationCode, ...]:
        return tuple(finding.code for finding in self.findings)

    def to_dict(self) -> dict[str, object]:
        return {
            "is_valid": self.is_valid,
            "orientation": self.orientation.value,
            "violations": [code.value for code in self.violations],
            "findings": [finding.to_dict() for finding in self.findings],
        }

    @classmethod
    def forward(cls) -> "RelationshipDirectionResult":
        return cls(RelationshipOrientation.FORWARD)

    @classmethod
    def reverse(cls) -> "RelationshipDirectionResult":
        return cls(RelationshipOrientation.REVERSE)

    @classmethod
    def invalid(
        cls, *findings: RelationshipDirectionFinding
    ) -> "RelationshipDirectionResult":
        return cls(RelationshipOrientation.INVALID, tuple(findings))


class RelationshipDirectionRuleError(ValueError):
    """Base error for relationship-direction rule failures."""


class RelationshipDirectionViolation(RelationshipDirectionRuleError):
    """Raised when a candidate relationship has invalid direction semantics."""

    def __init__(self, result: RelationshipDirectionResult) -> None:
        if not isinstance(result, RelationshipDirectionResult):
            raise TypeError("result must be a RelationshipDirectionResult.")
        if result.is_valid:
            raise ValueError("a valid result cannot raise a direction violation.")
        self.result = result
        codes = ", ".join(code.value for code in result.violations)
        super().__init__(f"relationship direction is invalid: {codes}.")


def evaluate_relationship_direction(
    accepted: RelationshipDefinition,
    candidate: RelationshipDefinition,
    direction: RelationshipDirection,
) -> RelationshipDirectionResult:
    """Classify a candidate as a valid forward or reverse relationship view."""
    _validate_inputs(accepted, candidate, direction)

    findings: list[RelationshipDirectionFinding] = []
    if accepted.runtime_mode != candidate.runtime_mode:
        findings.append(
            RelationshipDirectionFinding(
                RelationshipDirectionViolationCode.RUNTIME_MODE_MISMATCH,
                "candidate runtime mode differs from the accepted relationship.",
            )
        )

    same_endpoints = _same_reference(accepted.source, candidate.source) and _same_reference(
        accepted.target, candidate.target
    )
    reversed_endpoints = _same_reference(
        accepted.source, candidate.target
    ) and _same_reference(accepted.target, candidate.source)

    if same_endpoints:
        if not _same_type(candidate.relationship_type, direction.forward_type):
            findings.append(
                RelationshipDirectionFinding(
                    RelationshipDirectionViolationCode.RELATIONSHIP_TYPE_MISMATCH,
                    "forward orientation must use the declared forward relationship type.",
                )
            )
        return _result_or_orientation(findings, RelationshipOrientation.FORWARD)

    if reversed_endpoints:
        if not direction.allows_reverse:
            findings.append(
                RelationshipDirectionFinding(
                    RelationshipDirectionViolationCode.REVERSE_NOT_ALLOWED,
                    "the declared direction does not permit reverse interpretation.",
                )
            )
        else:
            reverse_type = direction.type_for_reverse()
            if reverse_type is None or not _same_type(
                candidate.relationship_type, reverse_type
            ):
                findings.append(
                    RelationshipDirectionFinding(
                        RelationshipDirectionViolationCode.RELATIONSHIP_TYPE_MISMATCH,
                        "reverse orientation must use the declared reverse relationship type.",
                    )
                )
        return _result_or_orientation(findings, RelationshipOrientation.REVERSE)

    findings.append(
        RelationshipDirectionFinding(
            RelationshipDirectionViolationCode.ENDPOINT_ORIENTATION_MISMATCH,
            "candidate endpoints are neither the accepted orientation nor its reversal.",
        )
    )
    return RelationshipDirectionResult.invalid(*findings)


def assert_relationship_direction(
    accepted: RelationshipDefinition,
    candidate: RelationshipDefinition,
    direction: RelationshipDirection,
) -> RelationshipOrientation:
    """Return candidate orientation or raise for invalid direction semantics."""
    result = evaluate_relationship_direction(accepted, candidate, direction)
    if not result.is_valid:
        raise RelationshipDirectionViolation(result)
    return result.orientation


def _result_or_orientation(
    findings: list[RelationshipDirectionFinding],
    orientation: RelationshipOrientation,
) -> RelationshipDirectionResult:
    if findings:
        return RelationshipDirectionResult.invalid(*findings)
    return RelationshipDirectionResult(orientation)


def _validate_inputs(
    accepted: RelationshipDefinition,
    candidate: RelationshipDefinition,
    direction: RelationshipDirection,
) -> None:
    if not isinstance(accepted, RelationshipDefinition):
        raise TypeError("accepted must be a RelationshipDefinition.")
    if not isinstance(candidate, RelationshipDefinition):
        raise TypeError("candidate must be a RelationshipDefinition.")
    if not isinstance(direction, RelationshipDirection):
        raise TypeError("direction must be a RelationshipDirection.")
    if not _same_type(accepted.relationship_type, direction.forward_type):
        raise RelationshipDirectionRuleError(
            "accepted relationship must use the direction's forward type."
        )


def _same_reference(left: RegistryReference, right: RegistryReference) -> bool:
    return (
        left.registry_id,
        left.record_id,
        left.version,
    ) == (
        right.registry_id,
        right.record_id,
        right.version,
    )


def _same_type(left: RelationshipType, right: RelationshipType) -> bool:
    return (
        left.relationship_type_id,
        left.relationship_type_code,
        left.version,
    ) == (
        right.relationship_type_id,
        right.relationship_type_code,
        right.version,
    )


__all__ = [
    "RelationshipDirectionFinding",
    "RelationshipDirectionResult",
    "RelationshipDirectionRuleError",
    "RelationshipDirectionViolation",
    "RelationshipDirectionViolationCode",
    "RelationshipOrientation",
    "assert_relationship_direction",
    "evaluate_relationship_direction",
]
