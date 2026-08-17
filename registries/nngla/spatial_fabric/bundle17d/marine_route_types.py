"""Governed Bundle 17D anonymous marine route type vocabulary."""
from __future__ import annotations

from .contracts import MarineRouteType


def marine_route_types() -> tuple[MarineRouteType, ...]:
    return (MarineRouteType(
        marine_route_type_code="MAINLAND_TO_OFFSHORE_ISLAND",
        canonical_label="Mainland to Offshore Island",
        connection_type="MAINLAND_TO_OFFSHORE_ISLAND",
        geometry_type_code="LINESTRING",
        start_anchor_role="MAINLAND_DEPARTURE",
        end_anchor_role="ISLAND_ARRIVAL",
        interior_spatial_requirement="OUTSIDE_SOVEREIGN_LAND_EXPECTED_MARINE",
        endpoint_spatial_requirement="ON_SOVEREIGN_BOUNDARY",
        may_cross_land=False,
        physical_qualification_requires_name=False,
        supports_history=True,
        status="ACTIVE",
        effective_from="2026-08-17",
        description="Anonymous physical sea route from the NoveGeo mainland coastline to one offshore island.",
    ),)


def marine_route_type_rows() -> tuple[dict[str, str], ...]:
    return tuple({
        "marine_route_type_code": row.marine_route_type_code,
        "canonical_label": row.canonical_label,
        "connection_type": row.connection_type,
        "geometry_type_code": row.geometry_type_code,
        "start_anchor_role": row.start_anchor_role,
        "end_anchor_role": row.end_anchor_role,
        "interior_spatial_requirement": row.interior_spatial_requirement,
        "endpoint_spatial_requirement": row.endpoint_spatial_requirement,
        "may_cross_land": str(row.may_cross_land).lower(),
        "physical_qualification_requires_name": str(row.physical_qualification_requires_name).lower(),
        "supports_history": str(row.supports_history).lower(),
        "status": row.status,
        "effective_from": row.effective_from,
        "description": row.description,
    } for row in marine_route_types())


__all__ = ["marine_route_types", "marine_route_type_rows"]
