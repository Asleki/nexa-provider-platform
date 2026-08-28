"""Immutable unresolved territorial residual evidence contracts."""
from __future__ import annotations

from .contracts import UnresolvedTerritorialResidual, stable_digest, stable_id


def build_residual(
    *, parent_administrative_area_id: str, geometry_wkb_hex: str,
    area_m2: float, adjacent_subject_ids: tuple[str, ...],
    originating_target_ids: tuple[str, ...], source_fingerprint: str,
    runtime_fingerprint: str, reason: str,
) -> UnresolvedTerritorialResidual:
    geometry_sha = stable_digest({"ewkbHex": geometry_wkb_hex})
    residual_id = stable_id("territorial-residual:nngla:", {
        "parent": parent_administrative_area_id,
        "geometrySha256": geometry_sha,
        "targets": sorted(originating_target_ids),
    })
    return UnresolvedTerritorialResidual(
        residual_id=residual_id,
        parent_administrative_area_id=parent_administrative_area_id,
        geometry_sha256=geometry_sha,
        geometry_wkb_hex=geometry_wkb_hex,
        area_m2=float(area_m2),
        adjacent_subject_ids=tuple(sorted(adjacent_subject_ids)),
        originating_target_ids=tuple(sorted(originating_target_ids)),
        source_fingerprint=source_fingerprint,
        runtime_fingerprint=runtime_fingerprint,
        reason=reason,
    )


__all__ = ["build_residual"]
