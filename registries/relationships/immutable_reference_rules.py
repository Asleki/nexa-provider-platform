"""Policy-level immutable reference comparison and enforcement rules.

M008.16.1 makes individual contract objects structurally immutable.  This
module adds replacement immutability: a caller cannot present a new object with
changed identity-bearing fields and treat it as an update of the accepted fact.

The rules remain storage-neutral and domain-neutral.  They do not resolve
records, decide transfer legality, create correction relationships, publish
events, or enforce direction, cardinality, provenance, or lifecycle policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from .immutable_reference_result import (
    ImmutableReferenceField,
    ImmutableReferenceFinding,
    ImmutableReferenceResult,
    ImmutableReferenceViolationCode,
)
from .registry_reference import RegistryReference
from .relationship_definition import RelationshipDefinition

RegistryReferenceIdentityKey: TypeAlias = tuple[str, str, int]
RelationshipIdentityKey: TypeAlias = tuple[
    str,
    str,
    str,
    RegistryReferenceIdentityKey,
    RegistryReferenceIdentityKey,
    str,
    int,
]


class ImmutableReferenceError(ValueError):
    """Base error for immutable-reference rule failures."""


class ImmutableReferenceViolation(ImmutableReferenceError):
    """Raised when a proposed replacement changes immutable identity."""

    def __init__(self, result: ImmutableReferenceResult) -> None:
        if not isinstance(result, ImmutableReferenceResult):
            raise TypeError("result must be an ImmutableReferenceResult.")
        if result.is_compatible:
            raise ValueError("a compatible result cannot raise an immutable violation.")
        self.result = result
        fields = ", ".join(field.value for field in result.changed_fields)
        super().__init__(f"immutable reference fields changed: {fields}.")


@dataclass(frozen=True, slots=True)
class _ComparisonRule:
    field: ImmutableReferenceField
    code: ImmutableReferenceViolationCode
    existing_value: object
    proposed_value: object

    def finding_if_changed(self) -> ImmutableReferenceFinding | None:
        if self.existing_value == self.proposed_value:
            return None
        return ImmutableReferenceFinding(
            self.code,
            self.field,
            self.existing_value,
            self.proposed_value,
        )


def registry_reference_identity_key(
    reference: RegistryReference,
) -> RegistryReferenceIdentityKey:
    """Return the explicit immutable identity of a registry-owned record."""
    if not isinstance(reference, RegistryReference):
        raise TypeError("reference must be a RegistryReference.")
    return (reference.registry_id, reference.record_id, reference.version)


def relationship_identity_key(
    relationship: RelationshipDefinition,
) -> RelationshipIdentityKey:
    """Return the immutable identity projection of one relationship fact."""
    if not isinstance(relationship, RelationshipDefinition):
        raise TypeError("relationship must be a RelationshipDefinition.")
    return (
        relationship.relationship_id,
        relationship.relationship_type.relationship_type_id,
        relationship.relationship_type.relationship_type_code,
        registry_reference_identity_key(relationship.source),
        registry_reference_identity_key(relationship.target),
        relationship.runtime_mode,
        relationship.version,
    )


def compare_registry_references(
    existing: RegistryReference,
    proposed: RegistryReference,
) -> ImmutableReferenceResult:
    """Compare accepted and proposed endpoint references field by field."""
    if not isinstance(existing, RegistryReference):
        raise TypeError("existing must be a RegistryReference.")
    if not isinstance(proposed, RegistryReference):
        raise TypeError("proposed must be a RegistryReference.")

    rules = (
        _ComparisonRule(
            ImmutableReferenceField.REGISTRY_ID,
            ImmutableReferenceViolationCode.REGISTRY_ID_CHANGED,
            existing.registry_id,
            proposed.registry_id,
        ),
        _ComparisonRule(
            ImmutableReferenceField.RECORD_ID,
            ImmutableReferenceViolationCode.RECORD_ID_CHANGED,
            existing.record_id,
            proposed.record_id,
        ),
        _ComparisonRule(
            ImmutableReferenceField.REFERENCE_VERSION,
            ImmutableReferenceViolationCode.REFERENCE_VERSION_CHANGED,
            existing.version,
            proposed.version,
        ),
    )
    return _result_from_rules(rules)


def compare_relationship_definitions(
    existing: RelationshipDefinition,
    proposed: RelationshipDefinition,
) -> ImmutableReferenceResult:
    """Compare all explicit immutable fields of two relationship definitions."""
    if not isinstance(existing, RelationshipDefinition):
        raise TypeError("existing must be a RelationshipDefinition.")
    if not isinstance(proposed, RelationshipDefinition):
        raise TypeError("proposed must be a RelationshipDefinition.")

    rules = (
        _ComparisonRule(
            ImmutableReferenceField.RELATIONSHIP_ID,
            ImmutableReferenceViolationCode.RELATIONSHIP_ID_CHANGED,
            existing.relationship_id,
            proposed.relationship_id,
        ),
        _ComparisonRule(
            ImmutableReferenceField.RELATIONSHIP_TYPE_ID,
            ImmutableReferenceViolationCode.RELATIONSHIP_TYPE_ID_CHANGED,
            existing.relationship_type.relationship_type_id,
            proposed.relationship_type.relationship_type_id,
        ),
        _ComparisonRule(
            ImmutableReferenceField.RELATIONSHIP_TYPE_CODE,
            ImmutableReferenceViolationCode.RELATIONSHIP_TYPE_CODE_CHANGED,
            existing.relationship_type.relationship_type_code,
            proposed.relationship_type.relationship_type_code,
        ),
        _ComparisonRule(
            ImmutableReferenceField.SOURCE_REGISTRY_ID,
            ImmutableReferenceViolationCode.SOURCE_REGISTRY_ID_CHANGED,
            existing.source.registry_id,
            proposed.source.registry_id,
        ),
        _ComparisonRule(
            ImmutableReferenceField.SOURCE_RECORD_ID,
            ImmutableReferenceViolationCode.SOURCE_RECORD_ID_CHANGED,
            existing.source.record_id,
            proposed.source.record_id,
        ),
        _ComparisonRule(
            ImmutableReferenceField.SOURCE_VERSION,
            ImmutableReferenceViolationCode.SOURCE_VERSION_CHANGED,
            existing.source.version,
            proposed.source.version,
        ),
        _ComparisonRule(
            ImmutableReferenceField.TARGET_REGISTRY_ID,
            ImmutableReferenceViolationCode.TARGET_REGISTRY_ID_CHANGED,
            existing.target.registry_id,
            proposed.target.registry_id,
        ),
        _ComparisonRule(
            ImmutableReferenceField.TARGET_RECORD_ID,
            ImmutableReferenceViolationCode.TARGET_RECORD_ID_CHANGED,
            existing.target.record_id,
            proposed.target.record_id,
        ),
        _ComparisonRule(
            ImmutableReferenceField.TARGET_VERSION,
            ImmutableReferenceViolationCode.TARGET_VERSION_CHANGED,
            existing.target.version,
            proposed.target.version,
        ),
        _ComparisonRule(
            ImmutableReferenceField.RUNTIME_MODE,
            ImmutableReferenceViolationCode.RUNTIME_MODE_CHANGED,
            existing.runtime_mode,
            proposed.runtime_mode,
        ),
        _ComparisonRule(
            ImmutableReferenceField.RELATIONSHIP_VERSION,
            ImmutableReferenceViolationCode.RELATIONSHIP_VERSION_CHANGED,
            existing.version,
            proposed.version,
        ),
    )
    return _result_from_rules(rules)


def assert_registry_reference_unchanged(
    existing: RegistryReference,
    proposed: RegistryReference,
) -> None:
    """Raise when a proposed endpoint reference redirects immutable identity."""
    _raise_if_incompatible(compare_registry_references(existing, proposed))


def assert_relationship_definition_unchanged(
    existing: RelationshipDefinition,
    proposed: RelationshipDefinition,
) -> None:
    """Raise when a proposed relationship replacement changes immutable identity."""
    _raise_if_incompatible(compare_relationship_definitions(existing, proposed))


def _result_from_rules(
    rules: tuple[_ComparisonRule, ...],
) -> ImmutableReferenceResult:
    findings = tuple(
        finding
        for rule in rules
        if (finding := rule.finding_if_changed()) is not None
    )
    return ImmutableReferenceResult(findings)


def _raise_if_incompatible(result: ImmutableReferenceResult) -> None:
    if not result.is_compatible:
        raise ImmutableReferenceViolation(result)


__all__ = [
    "ImmutableReferenceError",
    "ImmutableReferenceViolation",
    "RegistryReferenceIdentityKey",
    "RelationshipIdentityKey",
    "assert_registry_reference_unchanged",
    "assert_relationship_definition_unchanged",
    "compare_registry_references",
    "compare_relationship_definitions",
    "registry_reference_identity_key",
    "relationship_identity_key",
]
