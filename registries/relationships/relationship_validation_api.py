"""Validation-only application API for complete relationship packages.

M008.16.6 orchestrates existing immutable-reference, direction, constraint and
provenance rules.  A valid result means compatible, not persisted, approved,
authorised, or event-committed.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from .immutable_reference_rules import compare_relationship_definitions
from .relationship_api_contract import (
    RelationshipApiContract,
    RelationshipApiFinding,
    RelationshipApiOperation,
    RelationshipApiSubsystem,
    RelationshipValidationRequest,
    RelationshipValidationResult,
)
from .relationship_constraint_rules import evaluate_relationship_constraints
from .relationship_direction_rules import (
    RelationshipDirectionRuleError,
    RelationshipDirectionViolationCode,
    evaluate_relationship_direction,
)
from .relationship_provenance_rules import evaluate_relationship_provenance


class RelationshipApiExecutionError(ValueError):
    """Raised when the validation API cannot safely process a request."""


class RelationshipValidationViolation(RelationshipApiExecutionError):
    """Raised by assertion helpers for a processed but invalid package."""

    def __init__(self, result: RelationshipValidationResult) -> None:
        if not isinstance(result, RelationshipValidationResult):
            raise TypeError("result must be a RelationshipValidationResult.")
        if result.is_valid:
            raise ValueError("a valid result cannot raise a validation violation.")
        self.result = result
        codes = ", ".join(
            f"{finding.subsystem.value}:{finding.code}" for finding in result.findings
        )
        super().__init__(f"relationship package is invalid: {codes}.")


class RelationshipValidationApi:
    """Framework-neutral façade over the M008.16 relationship rule family."""

    def __init__(
        self,
        contract: RelationshipApiContract | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._contract = RelationshipApiContract() if contract is None else contract
        if not isinstance(self._contract, RelationshipApiContract):
            raise TypeError("contract must be a RelationshipApiContract or None.")
        if clock is not None and not callable(clock):
            raise TypeError("clock must be callable or None.")
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @property
    def contract(self) -> RelationshipApiContract:
        return self._contract

    def validate(self, request: RelationshipValidationRequest) -> RelationshipValidationResult:
        if not isinstance(request, RelationshipValidationRequest):
            raise TypeError("request must be a RelationshipValidationRequest.")
        if request.operation is not RelationshipApiOperation.VALIDATE:
            raise RelationshipApiExecutionError(
                f"unsupported relationship API operation: {request.operation.value}."
            )
        if not self._contract.supports(request.operation):
            raise RelationshipApiExecutionError(
                f"API contract does not support operation: {request.operation.value}."
            )

        completed_at = self._completed_at()
        findings: list[RelationshipApiFinding] = []

        if request.existing_relationship is not None:
            immutable_result = compare_relationship_definitions(
                request.existing_relationship, request.relationship
            )
            for finding in immutable_result.findings:
                findings.append(
                    RelationshipApiFinding(
                        RelationshipApiSubsystem.IMMUTABLE_REFERENCE,
                        finding.code.value,
                        (
                            f"immutable field '{finding.field.value}' changed from "
                            f"{finding.existing_value!r} to {finding.proposed_value!r}."
                        ),
                    )
                )

        try:
            direction_result = evaluate_relationship_direction(
                request.relationship, request.relationship, request.direction
            )
        except RelationshipDirectionRuleError as exc:
            findings.append(
                RelationshipApiFinding(
                    RelationshipApiSubsystem.DIRECTION,
                    RelationshipDirectionViolationCode.RELATIONSHIP_TYPE_MISMATCH.value,
                    str(exc),
                )
            )
        else:
            for finding in direction_result.findings:
                findings.append(
                    RelationshipApiFinding(
                        RelationshipApiSubsystem.DIRECTION,
                        finding.code.value,
                        finding.message,
                    )
                )

        constraint_result = evaluate_relationship_constraints(
            request.relationship, request.constraint, request.constraint_context
        )
        for finding in constraint_result.findings:
            findings.append(
                RelationshipApiFinding(
                    RelationshipApiSubsystem.CONSTRAINT,
                    finding.code.value,
                    finding.message,
                )
            )

        provenance_result = evaluate_relationship_provenance(
            request.relationship, request.provenance
        )
        for finding in provenance_result.findings:
            findings.append(
                RelationshipApiFinding(
                    RelationshipApiSubsystem.PROVENANCE,
                    finding.code.value,
                    finding.message,
                )
            )

        metadata = {
            "validation_only": True,
            "persisted": False,
            "approved": False,
        }
        if findings:
            return RelationshipValidationResult.invalid(
                request_id=request.request_id,
                operation=request.operation,
                completed_at=completed_at,
                findings=tuple(findings),
                api_name=self._contract.name,
                api_version=self._contract.version,
                metadata=metadata,
            )
        return RelationshipValidationResult.valid(
            request_id=request.request_id,
            operation=request.operation,
            completed_at=completed_at,
            api_name=self._contract.name,
            api_version=self._contract.version,
            metadata=metadata,
        )

    def execute(self, request: RelationshipValidationRequest) -> RelationshipValidationResult:
        return self.validate(request)

    def assert_valid(self, request: RelationshipValidationRequest) -> RelationshipValidationResult:
        result = self.validate(request)
        if not result.is_valid:
            raise RelationshipValidationViolation(result)
        return result

    def _completed_at(self) -> datetime:
        value = self._clock()
        if not isinstance(value, datetime):
            raise RelationshipApiExecutionError("clock must return a datetime.")
        if value.tzinfo is None or value.utcoffset() is None:
            raise RelationshipApiExecutionError(
                "clock must return a timezone-aware datetime."
            )
        return value.astimezone(timezone.utc)


def validate_relationship(
    request: RelationshipValidationRequest,
    *,
    contract: RelationshipApiContract | None = None,
    clock: Callable[[], datetime] | None = None,
) -> RelationshipValidationResult:
    """Validate one complete relationship package without side effects."""
    return RelationshipValidationApi(contract=contract, clock=clock).validate(request)


def assert_relationship_validation(
    request: RelationshipValidationRequest,
    *,
    contract: RelationshipApiContract | None = None,
    clock: Callable[[], datetime] | None = None,
) -> RelationshipValidationResult:
    """Return a valid result or raise a structured validation violation."""
    return RelationshipValidationApi(contract=contract, clock=clock).assert_valid(request)


__all__ = [
    "RelationshipApiExecutionError",
    "RelationshipValidationApi",
    "RelationshipValidationViolation",
    "assert_relationship_validation",
    "validate_relationship",
]
