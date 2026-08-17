"""Bundle 17H governed address allocation and display policy vocabulary."""
from __future__ import annotations

from .contracts import AddressAllocationPolicy, AddressAllocationPolicyDefinition


def allocation_policy_rows() -> tuple[dict[str, str], ...]:
    rows = (
        ("CONTINUOUS", "ROAD_OR_GOVERNED_CORRIDOR", "NO_AUTOMATIC_RESET", 1),
        ("LOCAL_RESET", "LOCAL_GOVERNED_SCOPE", "RESET_PER_LOCAL_SCOPE", 1),
        ("SEGMENT_RESET", "ROAD_SEGMENT", "RESET_PER_SEGMENT", 1),
        ("ODD_EVEN", "ROAD_OR_SEGMENT_SIDE", "SIDE_SPECIFIC_PARITY", 2),
        ("SEQUENTIAL", "EXPLICIT_SERIES", "MONOTONIC_NO_REUSE", 1),
        ("CUSTOM_GOVERNED", "CUSTOM_GOVERNED_SCOPE", "RULESET_REQUIRED", 1),
    )
    return tuple({
        "policy_code": code,
        "allocation_scope": scope,
        "reset_semantics": reset,
        "default_sequence_step": str(step),
        "duplicate_visible_number_cross_scope_allowed": "true",
        "same_scope_collision_policy": "FAIL_CLOSED",
        "status": "ACTIVE",
        "description": f"Governed {code} address-number allocation policy.",
    } for code, scope, reset, step in rows)


def allocation_policies() -> tuple[AddressAllocationPolicyDefinition, ...]:
    return tuple(AddressAllocationPolicyDefinition(
        policy_code=AddressAllocationPolicy(row["policy_code"]),
        allocation_scope=row["allocation_scope"], reset_semantics=row["reset_semantics"],
        default_sequence_step=int(row["default_sequence_step"]),
        duplicate_visible_number_cross_scope_allowed=row["duplicate_visible_number_cross_scope_allowed"] == "true",
        same_scope_collision_policy=row["same_scope_collision_policy"], status=row["status"],
    ) for row in allocation_policy_rows())


def address_format_rule_rows() -> tuple[dict[str, str], ...]:
    return (
        {"format_rule_code": "INTEGER", "number_pattern": r"^[0-9]+$", "canonical_example": "14", "suffix_allowed": "false", "unit_designator_separate": "true", "status": "ACTIVE", "description": "Unsigned integer premise number."},
        {"format_rule_code": "INTEGER_SUFFIX", "number_pattern": r"^[0-9]+[A-Z]$", "canonical_example": "14B", "suffix_allowed": "true", "unit_designator_separate": "true", "status": "ACTIVE", "description": "Integer plus governed uppercase suffix."},
        {"format_rule_code": "GOVERNED_TEXT", "number_pattern": r"^[0-9A-Z][0-9A-Z/-]{0,15}$", "canonical_example": "14/2", "suffix_allowed": "true", "unit_designator_separate": "true", "status": "ACTIVE", "description": "Bounded governed human-readable address token."},
    )


__all__ = ["allocation_policy_rows", "allocation_policies", "address_format_rule_rows"]
