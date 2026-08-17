from datetime import date
import pytest
from registries.nngla.spatial_fabric.bundle17g import (
    CadastralSeriesDefinition,
    MemoryParcelReferenceAllocator,
    ParcelGeometryCandidate,
    cadastral_geometry_is_qualified,
    form_parcel_candidate,
    geometry_findings,
    qualify_parcel_candidate,
    register_qualified_parcel,
)


def _fixture(overlap="DEFERRED_NO_REGISTERED_PARCELS"):
    candidate = form_parcel_candidate(
        physical_ground_reference="NG-SPT-000100", proposed_land_use_code="AGRICULTURAL", source_reference="test:parcel",
        proposed_geometry_id="NG-GEO-900100", survey_status="SURVEYED"
    )
    reservation = MemoryParcelReferenceAllocator(start_sequence=8890).reserve(candidate, CadastralSeriesDefinition("12", "004"))
    geometry = ParcelGeometryCandidate(
        "parcelgeo:nngla:test", candidate.parcel_candidate_id, "NG-GEO-900100", "POLYGON", "NG-CRS-EPSG4326",
        True, True, "INSIDE_SOVEREIGN_LAND", overlap, "NG-SRV-900100", "SURVEYED", "test:survey"
    )
    return candidate, reservation, geometry


def test_cadastral_geometry_requires_real_polygon_survey_and_sovereign_land():
    _, _, geometry = _fixture()
    assert cadastral_geometry_is_qualified(geometry)
    assert geometry_findings(geometry) == ()
    with pytest.raises(ValueError):
        ParcelGeometryCandidate(
            "parcelgeo:nngla:line", "parcelcand:nngla:test", "NG-GEO-900101", "LINESTRING", "NG-CRS-EPSG4326",
            True, True, "INSIDE_SOVEREIGN_LAND", "CLEAR", "NG-SRV-900101", "SURVEYED", "test"
        )


def test_overlap_conflict_fails_closed():
    candidate, reservation, geometry = _fixture(overlap="OVERLAPS_REGISTERED_PARCEL")
    assert not cadastral_geometry_is_qualified(geometry)
    result = qualify_parcel_candidate(candidate, reservation, geometry)
    assert result.qualification_status == "FAIL"
    assert "PARCEL_OVERLAP_CONFLICT" in result.findings


def test_qualified_candidate_registers_by_reusing_locked_parcel_record_contract():
    candidate, reservation, geometry = _fixture()
    result = qualify_parcel_candidate(candidate, reservation, geometry)
    assert result.recognition_ready
    parcel = register_qualified_parcel(candidate, reservation, geometry, effective_on=date(2026, 8, 17), source_reference="test:registration")
    assert parcel.parcel_id == "NV-12-004-8890"
    assert parcel.geometry_reference == "NG-GEO-900100"
    assert parcel.cadastral_series == "NV-12-004"
    assert parcel.parcel_status.value == "REGISTERED"
