"""Bundle 17D qualification facade."""
from __future__ import annotations

from registries.nngla.spatial_fabric.bundle17c import bundle17c_is_qualified

from .feature_type_extensions import effective_feature_type_codes
from .marine_qualification import derive_marine_spatial_qualification_results, marine_qualification_findings
from .marine_route_types import marine_route_types
from .marine_sources import marine_source_findings


def bundle17d_is_qualified() -> bool:
    rows = derive_marine_spatial_qualification_results()
    return (
        bundle17c_is_qualified()
        and not marine_source_findings()
        and not marine_qualification_findings(rows)
        and "OCEAN" in effective_feature_type_codes()
        and len(marine_route_types()) == 1
        and all(row.qualification_status in {"PASS", "PASS_WITH_KNOWN_GEOMETRY_LIMITATION"} for row in rows)
    )


__all__ = ["bundle17d_is_qualified"]
