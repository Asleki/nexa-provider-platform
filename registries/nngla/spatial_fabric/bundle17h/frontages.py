"""Bundle 17H frontage relationship formation without inventing physical access."""
from __future__ import annotations

from ._shared import stable_id
from .contracts import AddressableSiteCandidate, RoadFrontageCandidate, RoadSegmentCandidate


def form_frontage_candidate(
    site: AddressableSiteCandidate,
    segment: RoadSegmentCandidate,
    *, frontage_role: str = "PRIMARY", access_status: str = "PROPOSED",
    qualification_status: str = "PENDING_GEOMETRY_OR_SURVEY", source_reference: str,
) -> RoadFrontageCandidate:
    if site.road_id and site.road_id != segment.road_id:
        raise ValueError("site and frontage segment must belong to the same canonical road")
    frontage_id = stable_id("frontage:nngla:", site.site_id, segment.road_segment_id, frontage_role)
    return RoadFrontageCandidate(
        frontage_id=frontage_id, site_id=site.site_id, road_id=segment.road_id,
        road_segment_id=segment.road_segment_id, frontage_role=frontage_role,
        access_status=access_status, qualification_status=qualification_status, source_reference=source_reference,
    )


__all__ = ["form_frontage_candidate"]
