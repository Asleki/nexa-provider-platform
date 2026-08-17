"""Bundle 17G cadastral polygon qualification without creating imaginary parcel geometry."""
from __future__ import annotations
from .contracts import ParcelGeometryCandidate


def geometry_findings(candidate: ParcelGeometryCandidate) -> tuple[str, ...]:
    findings = []
    if not candidate.ring_closed: findings.append("RING_NOT_CLOSED")
    if not candidate.geometry_valid: findings.append("GEOMETRY_INVALID")
    if candidate.sovereign_land_relation not in {"INSIDE_SOVEREIGN_LAND", "ON_SOVEREIGN_BOUNDARY"}:
        findings.append("NOT_SOVEREIGN_LAND")
    if candidate.overlap_status not in {"CLEAR", "DEFERRED_NO_REGISTERED_PARCELS"}:
        findings.append("PARCEL_OVERLAP_CONFLICT")
    if not candidate.survey_id: findings.append("SURVEY_REQUIRED")
    if candidate.geometry_status not in {"SURVEYED", "QUALIFIED"}: findings.append("GEOMETRY_NOT_SURVEYED")
    return tuple(findings)


def cadastral_geometry_is_qualified(candidate: ParcelGeometryCandidate) -> bool:
    return not geometry_findings(candidate)


__all__ = ["geometry_findings", "cadastral_geometry_is_qualified"]
