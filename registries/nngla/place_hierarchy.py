"""P006.7.4 hierarchy qualification independent of authoritative geometry."""
from __future__ import annotations
from .places import PlaceReference
from .administrative_areas import AdministrativeArea

def qualify_place_hierarchy(places: tuple[PlaceReference, ...], areas: tuple[AdministrativeArea, ...]) -> tuple[str, ...]:
    findings: list[str] = []
    place_ids = {p.source_place_code for p in places}
    if len(place_ids) != len(places):
        findings.append("duplicate-place-source-identity")
    capitals = [p for p in places if p.is_national_capital]
    if len(capitals) != 1:
        findings.append("national-capital-count-must-equal-one")
    for p in places:
        if p.parent_source_place_code and p.parent_source_place_code not in place_ids:
            findings.append(f"missing-place-parent:{p.source_place_code}:{p.parent_source_place_code}")
        if p.has_authoritative_geometry:
            findings.append(f"unexpected-authoritative-place-geometry:{p.source_place_code}")
    admin_sources = {a.source_record_id for a in areas}
    allowed_roots = {"country:novegeo"} | place_ids | admin_sources
    for a in areas:
        if a.parent_source_record_id not in allowed_roots:
            findings.append(f"missing-admin-parent:{a.source_record_id}:{a.parent_source_record_id}")
        if not a.is_nonspatial_ready:
            findings.append(f"admin-not-ready-nonspatial:{a.source_record_id}")
    return tuple(findings)

__all__ = ["qualify_place_hierarchy"]
