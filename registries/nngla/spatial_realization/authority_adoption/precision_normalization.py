"""Governed precision normalization for Delivery 3 R1.

No tolerance is inferred from area. Source-exact is the default. A comparison
geometry can move only under an explicit, hash-bound common precision policy.
The immutable source geometry remains separately hash-bound in every receipt.
"""
from __future__ import annotations

from .contracts import PrecisionMode, PrecisionPolicy, SOURCE_EXACT_PRECISION


def governed_common_precision_policy(
    *, policy_id: str, grid_size_degrees: float, evidence_reference: str, policy_version: int = 1
) -> PrecisionPolicy:
    return PrecisionPolicy(
        policy_id=policy_id,
        mode=PrecisionMode.GOVERNED_COMMON_PRECISION,
        grid_size_degrees=grid_size_degrees,
        evidence_reference=evidence_reference,
        policy_version=policy_version,
    )


def normalization_expression(alias: str, policy: PrecisionPolicy) -> tuple[str, tuple[object, ...]]:
    """Return a PostGIS expression and parameters for one geometry alias."""
    if policy.mode is PrecisionMode.SOURCE_COORDINATES_EXACT_NO_GENERAL_SNAP:
        return alias, ()
    return f"ST_ReducePrecision({alias}, %s)", (float(policy.grid_size_degrees),)


def numerical_residue(*, raw_value: float, evaluated_value: float, policy: PrecisionPolicy) -> bool:
    return (
        policy.mode is PrecisionMode.GOVERNED_COMMON_PRECISION
        and float(raw_value) > 0.0
        and float(evaluated_value) == 0.0
    )


__all__ = [
    "SOURCE_EXACT_PRECISION", "governed_common_precision_policy",
    "normalization_expression", "numerical_residue",
]
