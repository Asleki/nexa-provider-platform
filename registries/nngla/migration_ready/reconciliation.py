"""Strict target reconciliation for the locked Bundle 17E spatial fabric."""
from __future__ import annotations

from collections.abc import Mapping

from .contracts import ReconciliationAction, ReconciliationItem


def reconcile_spatial_target(
    target_snapshot,
    crosswalks: Mapping[str, object],
    geometries: Mapping[str, object],
) -> tuple[ReconciliationItem, ...]:
    """Classify every expected spatial point as insert, exact reuse or conflict.

    The target snapshot is intentionally duck-typed to the locked
    ``TargetSpatialSnapshot`` contract. A mapping alone is not enough for reuse:
    canonical feature, active geometry mapping and geometry identity must all
    agree. Orphan/colliding identifiers fail closed.
    """
    if not getattr(target_snapshot, "available", True):
        raise ValueError("live PostgreSQL target is unavailable")

    occupied_spatial = set(getattr(target_snapshot, "occupied_spatial_ids", ()))
    occupied_geometry = set(getattr(target_snapshot, "occupied_geometry_ids", ()))
    target_crosswalks = dict(getattr(target_snapshot, "candidate_crosswalks", {}) or {})
    geometry_by_subject = dict(getattr(target_snapshot, "geometry_by_subject", {}) or {})

    out: list[ReconciliationItem] = []
    for candidate_id, crosswalk in crosswalks.items():
        if candidate_id not in geometries:
            out.append(
                ReconciliationItem(
                    candidate_id,
                    getattr(crosswalk, "canonical_spatial_point_id"),
                    "UNRESOLVED",
                    ReconciliationAction.CONFLICT,
                    "EXPECTED_GEOMETRY_MISSING_FROM_LOCKED_SOURCE",
                )
            )
            continue

        geometry = geometries[candidate_id]
        canonical_id = getattr(crosswalk, "canonical_spatial_point_id")
        geometry_id = getattr(geometry, "geometry_id")
        mapped_id = target_crosswalks.get(candidate_id)
        active_geometry_id = geometry_by_subject.get(canonical_id)
        canonical_occupied = canonical_id in occupied_spatial
        geometry_occupied = geometry_id in occupied_geometry

        if mapped_id is not None:
            if mapped_id != canonical_id:
                action = ReconciliationAction.CONFLICT
                reason = "CROSSWALK_CANONICAL_ID_MISMATCH"
            elif not canonical_occupied:
                action = ReconciliationAction.CONFLICT
                reason = "CROSSWALK_POINTS_TO_MISSING_CANONICAL_FEATURE"
            elif active_geometry_id != geometry_id:
                action = ReconciliationAction.CONFLICT
                reason = "ACTIVE_GEOMETRY_MISMATCH"
            elif not geometry_occupied:
                action = ReconciliationAction.CONFLICT
                reason = "GEOMETRY_MAPPING_POINTS_TO_MISSING_GEOMETRY"
            else:
                action = ReconciliationAction.REUSE_CANONICAL
                reason = "EXACT_POSTGRESQL_STATE_MATCH"
        else:
            if canonical_occupied:
                action = ReconciliationAction.CONFLICT
                reason = "CANONICAL_ID_OCCUPIED_WITHOUT_EXPECTED_CROSSWALK"
            elif active_geometry_id is not None:
                action = ReconciliationAction.CONFLICT
                reason = "SUBJECT_HAS_UNEXPECTED_ACTIVE_GEOMETRY"
            elif geometry_occupied:
                action = ReconciliationAction.CONFLICT
                reason = "GEOMETRY_ID_ALREADY_OCCUPIED"
            else:
                action = ReconciliationAction.INSERT_NEW
                reason = "TARGET_IDENTITIES_AVAILABLE"

        out.append(ReconciliationItem(candidate_id, canonical_id, geometry_id, action, reason))

    expected = set(crosswalks)
    unexpected = set(target_crosswalks) - expected
    if unexpected:
        # The spatial dataset query should only return this dataset/version. Any
        # extra candidate is drift and must stop migration rather than be ignored.
        for candidate_id in sorted(unexpected):
            out.append(
                ReconciliationItem(
                    candidate_id,
                    target_crosswalks[candidate_id],
                    geometry_by_subject.get(target_crosswalks[candidate_id], "UNRESOLVED"),
                    ReconciliationAction.CONFLICT,
                    "UNEXPECTED_TARGET_CROSSWALK_FOR_SPATIAL_DATASET",
                )
            )
    return tuple(out)


def conflict_items(items: tuple[ReconciliationItem, ...]) -> tuple[ReconciliationItem, ...]:
    return tuple(item for item in items if item.action is ReconciliationAction.CONFLICT)


def assert_no_conflicts(items: tuple[ReconciliationItem, ...]) -> None:
    conflicts = conflict_items(items)
    if conflicts:
        sample = ", ".join(
            f"{item.coordinate_candidate_id}:{item.reason}" for item in conflicts[:8]
        )
        raise ValueError(f"NNGLA target reconciliation failed closed ({len(conflicts)} conflicts): {sample}")


__all__ = ["reconcile_spatial_target", "conflict_items", "assert_no_conflicts"]
