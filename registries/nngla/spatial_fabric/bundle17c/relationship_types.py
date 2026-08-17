"""Governed Bundle 17C spatial relationship vocabulary."""
from __future__ import annotations

from .contracts import RelationshipType


def relationship_type_rows() -> tuple[dict[str, str], ...]:
    rows = (
        (RelationshipType.CONTAINS, "Contains", "DIRECTIONAL", RelationshipType.WITHIN, False, True, False, "Topological containment"),
        (RelationshipType.WITHIN, "Within", "DIRECTIONAL", RelationshipType.CONTAINS, False, True, False, "Inverse topological containment"),
        (RelationshipType.INTERSECTS, "Intersects", "SYMMETRIC", RelationshipType.INTERSECTS, True, True, False, "Geometries share any spatial portion"),
        (RelationshipType.CROSSES, "Crosses", "DIRECTIONAL", RelationshipType.CROSSES, False, True, False, "Subject traverses object geometry"),
        (RelationshipType.TOUCHES, "Touches", "SYMMETRIC", RelationshipType.TOUCHES, True, True, False, "Boundaries meet without interior overlap"),
        (RelationshipType.OVERLAPS, "Overlaps", "SYMMETRIC", RelationshipType.OVERLAPS, True, True, False, "Same-dimension geometries share interior area/length"),
        (RelationshipType.ADJACENT_TO, "Adjacent To", "SYMMETRIC", RelationshipType.ADJACENT_TO, True, True, False, "Governed adjacency relation"),
        (RelationshipType.NEAR, "Near", "SYMMETRIC", RelationshipType.NEAR, True, True, True, "Distance-threshold relationship"),
        (RelationshipType.FRONTS, "Fronts", "DIRECTIONAL", RelationshipType.FRONTS, False, True, False, "Site or parcel has governed frontage"),
        (RelationshipType.CONNECTED_TO, "Connected To", "SYMMETRIC", RelationshipType.CONNECTED_TO, True, True, False, "Physical/network connection"),
    )
    return tuple({
        "relationship_type_code": code.value,
        "canonical_label": label,
        "directionality": direction,
        "inverse_relationship_type_code": inverse.value,
        "is_symmetric": str(symmetric).lower(),
        "requires_geometry_evidence": str(requires_geometry).lower(),
        "requires_distance_threshold": str(requires_distance).lower(),
        "distance_unit": "governed_unit_required" if requires_distance else "",
        "supports_point": "true",
        "supports_linestring": "true",
        "supports_polygon": "true",
        "topological_semantics": semantics,
        "compatibility_semantics": "RELATIONSHIP_FACT_IS_SEPARATE_FROM_POLICY_OUTCOME",
        "status": "ACTIVE",
        "effective_from": "2026-08-17",
        "description": f"Bundle 17C governed {label.lower()} relationship.",
    } for code, label, direction, inverse, symmetric, requires_geometry, requires_distance, semantics in rows)


__all__ = ["relationship_type_rows"]
