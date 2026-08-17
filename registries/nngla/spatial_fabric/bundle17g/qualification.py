"""Bundle 17G qualification preserving empty Day-Zero legal registers."""
from __future__ import annotations
from datetime import date

from registries.nngla.bundle15c_source import load_land_use_codes, load_parcel_bootstrap
from ._shared import DAY_ZERO_PARCEL_PATH, csv_rows
from .artifacts import artifact_drift_findings, artifact_paths
from .cadastral_series import load_policy
from .contracts import CadastralSeriesDefinition, ParcelGeometryCandidate
from .parcel_candidates import form_parcel_candidate
from .recognition import qualify_parcel_candidate, register_qualified_parcel
from .reference_reservations import MemoryParcelReferenceAllocator


def bundle17g_findings() -> tuple[str, ...]:
    findings = []
    if load_parcel_bootstrap() != () or csv_rows(DAY_ZERO_PARCEL_PATH) != ():
        findings.append("DAY_ZERO_PARCEL_REGISTER_MUST_REMAIN_EMPTY")
    if len(load_land_use_codes()) != 13:
        findings.append("LAND_USE_VOCABULARY_DRIFT")
    try:
        policy = load_policy()
        if policy.administrative_area_dependency != "INDEPENDENT_OF_ADMINISTRATIVE_BOUNDARIES":
            findings.append("CADASTRAL_ZONE_ADMINISTRATIVE_COUPLING")
    except Exception as exc:
        findings.append(f"CADASTRAL_SERIES_POLICY_INVALID:{exc}")
    findings.extend(artifact_drift_findings())
    paths = artifact_paths()
    for key in ("parcel_candidates", "parcel_reservations", "parcel_geometry_candidates", "parcel_lineage_candidates", "parcel_bootstrap_v002"):
        if paths[key].is_file() and csv_rows(paths[key]):
            findings.append(f"FABRICATED_DAY_ZERO_ROWS:{key}")

    # In-memory proof only: no governed CSV or PostgreSQL writes are performed.
    try:
        candidate = form_parcel_candidate(
            physical_ground_reference="NG-SPT-000001", proposed_land_use_code="AGRICULTURAL",
            proposed_geometry_id="NG-GEO-900001", survey_status="SURVEYED",
            source_reference="qualification:bundle17g", runtime_mode="simulation",
        )
        series = CadastralSeriesDefinition("12", "004")
        reservation = MemoryParcelReferenceAllocator(start_sequence=8890).reserve(candidate, series)
        geometry = ParcelGeometryCandidate(
            parcel_geometry_candidate_id="parcelgeo:nngla:qualification", parcel_candidate_id=candidate.parcel_candidate_id,
            geometry_id="NG-GEO-900001", geometry_type_code="POLYGON", crs_code="NG-CRS-EPSG4326",
            ring_closed=True, geometry_valid=True, sovereign_land_relation="INSIDE_SOVEREIGN_LAND",
            overlap_status="DEFERRED_NO_REGISTERED_PARCELS", survey_id="NG-SRV-900001", geometry_status="SURVEYED",
            source_reference="qualification:bundle17g",
        )
        result = qualify_parcel_candidate(candidate, reservation, geometry)
        if not result.recognition_ready: findings.append("IN_MEMORY_PARCEL_RECOGNITION_NOT_READY")
        parcel = register_qualified_parcel(candidate, reservation, geometry, effective_on=date(2026, 8, 17), source_reference="qualification:bundle17g")
        if parcel.parcel_id != "NV-12-004-8890": findings.append("PARCEL_REFERENCE_SEMANTICS_DRIFT")
    except Exception as exc:
        findings.append(f"IN_MEMORY_OPERATIONAL_PROOF_FAILED:{exc}")
    return tuple(findings)


def bundle17g_is_qualified() -> bool:
    return not bundle17g_findings()


__all__ = ["bundle17g_findings", "bundle17g_is_qualified"]
