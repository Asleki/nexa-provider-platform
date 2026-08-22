"""Qualified parent/child spatial evidence for Bundle 19A."""
from __future__ import annotations

from functools import lru_cache

from ._shared import EFFECT_SCOPE, stable_id
from .contracts import PlaceSpatialRelationshipEvidence
from .footprints import derive_settlement_footprints
from .geometry import haversine_m, point_relation
from .siting import derive_place_reference_points
from .source import load_settlement_requirements


@lru_cache(maxsize=1)
def derive_place_spatial_relationships() -> tuple[PlaceSpatialRelationshipEvidence, ...]:
    requirements = {row.source_place_code: row for row in load_settlement_requirements()}
    points = {row.source_place_code: row for row in derive_place_reference_points()}
    footprints = {row.source_place_code: row for row in derive_settlement_footprints()}
    results: list[PlaceSpatialRelationshipEvidence] = []
    for child_source, requirement in sorted(requirements.items(), key=lambda item: int(item[0].rsplit("-", 1)[1])):
        parent_source = requirement.parent_source_place_code
        if not parent_source:
            continue
        parent_req = requirements[parent_source]
        child = points[child_source]
        parent = points[parent_source]
        distance_m = haversine_m(child.longitude, child.latitude, parent.longitude, parent.latitude)
        parent_footprint = footprints.get(parent_source)
        if parent_footprint is None:
            relation = "PARENT_HAS_NO_FOOTPRINT"
        else:
            relation = "WITHIN" if point_relation((child.longitude, child.latitude), parent_footprint.ring) in {"INSIDE", "BOUNDARY"} else "OUTSIDE"
        results.append(PlaceSpatialRelationshipEvidence(
            relationship_evidence_id=stable_id(
                "placerel:nngla:", child.place_id, parent.place_id, round(distance_m, 3), relation, "SOURCE_HIERARCHY_SPATIALLY_EVALUATED_V1"
            ),
            child_place_id=child.place_id,
            child_source_place_code=child_source,
            parent_place_id=parent.place_id,
            parent_source_place_code=parent_source,
            distance_m=round(distance_m, 3),
            parent_footprint_relation=relation,
            relationship_basis=(
                f"SOURCE_PARENT={parent_req.source_place_code};SOURCE_HIERARCHY_PRESERVED;"
                "TOPOLOGICAL_RELATION_REPORTED_AS_EVIDENCE_NOT_LEGAL_CONTAINMENT"
            ),
            qualification_status="PASS",
            runtime_effect_scope=EFFECT_SCOPE,
        ))
    if len(results) != 668:
        raise ValueError(f"expected 668 direct source-parent spatial evidence rows, found {len(results)}")
    return tuple(results)


__all__ = ["derive_place_spatial_relationships"]
