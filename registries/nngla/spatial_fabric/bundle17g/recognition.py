"""Bundle 17G survey qualification, recognition and final registration adapter."""
from __future__ import annotations
from datetime import date

from registries.nngla.parcels import ParcelRecord, ParcelStatus
from ._shared import LAND_USE_PATH, csv_rows
from .contracts import ParcelCandidateRecord, ParcelGeometryCandidate, ParcelQualificationResult, ParcelReferenceReservation
from .parcel_geometry import cadastral_geometry_is_qualified


def qualify_parcel_candidate(
    candidate: ParcelCandidateRecord,
    reservation: ParcelReferenceReservation,
    geometry: ParcelGeometryCandidate,
) -> ParcelQualificationResult:
    land_use_codes = {row["land_use_code"] for row in csv_rows(LAND_USE_PATH)}
    ground_distinct = candidate.physical_ground_reference != reservation.parcel_id
    reservation_ok = reservation.parcel_candidate_id == candidate.parcel_candidate_id and not reservation.legal_effect and not reservation.canonical_parcel_registered
    geometry_ok = geometry.parcel_candidate_id == candidate.parcel_candidate_id and geometry.geometry_id == candidate.proposed_geometry_id and cadastral_geometry_is_qualified(geometry)
    survey_ok = bool(geometry.survey_id and candidate.survey_status in {"SURVEYED", "QUALIFIED"})
    land_use_ok = candidate.proposed_land_use_code in land_use_codes
    sovereign_ok = geometry.sovereign_land_relation in {"INSIDE_SOVEREIGN_LAND", "ON_SOVEREIGN_BOUNDARY"}
    overlap_ok = geometry.overlap_status in {"CLEAR", "DEFERRED_NO_REGISTERED_PARCELS"}
    ready = all((ground_distinct, reservation_ok, geometry_ok, survey_ok, land_use_ok, sovereign_ok, overlap_ok))
    findings = []
    if not ground_distinct: findings.append("PHYSICAL_GROUND_MUST_NOT_BE_PARCEL_ID")
    if not reservation_ok: findings.append("REFERENCE_RESERVATION_INVALID")
    if not geometry_ok: findings.append("CADASTRAL_GEOMETRY_INVALID")
    if not survey_ok: findings.append("SURVEY_NOT_QUALIFIED")
    if not land_use_ok: findings.append("LAND_USE_CODE_INVALID")
    if not sovereign_ok: findings.append("PARCEL_NOT_ON_SOVEREIGN_LAND")
    if not overlap_ok: findings.append("PARCEL_OVERLAP_CONFLICT")
    return ParcelQualificationResult(
        parcel_candidate_id=candidate.parcel_candidate_id, parcel_id=reservation.parcel_id,
        physical_ground_distinct=ground_distinct, reference_reserved=reservation_ok, geometry_valid=geometry_ok,
        survey_valid=survey_ok, land_use_valid=land_use_ok, sovereign_land_valid=sovereign_ok,
        overlap_clear_or_deferred=overlap_ok, recognition_ready=ready,
        qualification_status="PASS" if ready else "FAIL", findings=";".join(findings),
    )


def register_qualified_parcel(
    candidate: ParcelCandidateRecord, reservation: ParcelReferenceReservation, geometry: ParcelGeometryCandidate,
    *, effective_on: date, source_reference: str,
) -> ParcelRecord:
    result = qualify_parcel_candidate(candidate, reservation, geometry)
    if not result.recognition_ready:
        raise ValueError(f"parcel candidate is not recognition-ready: {result.findings}")
    return ParcelRecord(
        parcel_id=reservation.parcel_id, parent_parcel_id=None,
        cadastral_series=f"NV-{reservation.cadastral_zone}-{reservation.cadastral_series}",
        parcel_sequence=reservation.parcel_sequence, parcel_status=ParcelStatus.REGISTERED,
        geometry_reference=geometry.geometry_id, land_use_code=candidate.proposed_land_use_code,
        survey_status="QUALIFIED", created_effective_at=effective_on, retired_effective_at=None,
        source_reference=source_reference,
    )


__all__ = ["qualify_parcel_candidate", "register_qualified_parcel"]
