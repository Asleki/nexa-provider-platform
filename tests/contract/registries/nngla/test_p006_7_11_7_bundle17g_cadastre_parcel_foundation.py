from datetime import date
from registries.nngla.bundle15c_source import load_parcel_bootstrap
from registries.nngla.spatial_fabric.bundle17g import (
    CadastralSeriesDefinition,
    MemoryParcelReferenceAllocator,
    ParcelGeometryCandidate,
    ParcelLineageCandidate,
    bundle17g_is_qualified,
    form_parcel_candidate,
    promote_lineage_candidate,
    qualify_parcel_candidate,
    register_qualified_parcel,
)
from registries.nngla.spatial_fabric.bundle17g.artifacts import artifact_rows


def test_bundle17g_contract_keeps_physical_ground_candidate_reference_and_registered_parcel_semantically_distinct():
    candidate = form_parcel_candidate(
        physical_ground_reference="NG-SPT-000300", proposed_land_use_code="RESIDENTIAL", source_reference="contract:ground",
        proposed_geometry_id="NG-GEO-900300", survey_status="SURVEYED"
    )
    reservation = MemoryParcelReferenceAllocator(start_sequence=1).reserve(candidate, CadastralSeriesDefinition("01", "001"))
    assert candidate.physical_ground_reference == "NG-SPT-000300"
    assert candidate.parcel_candidate_id.startswith("parcelcand:nngla:")
    assert reservation.parcel_id == "NV-01-001-0001"
    assert not reservation.canonical_parcel_registered


def test_bundle17g_contract_can_recognize_real_surveyed_polygon_without_populating_day_zero_registers():
    candidate = form_parcel_candidate(
        physical_ground_reference="NG-SPT-000301", proposed_land_use_code="RESIDENTIAL", source_reference="contract:ground",
        proposed_geometry_id="NG-GEO-900301", survey_status="SURVEYED"
    )
    reservation = MemoryParcelReferenceAllocator().reserve(candidate, CadastralSeriesDefinition("01", "001"))
    geometry = ParcelGeometryCandidate(
        "parcelgeo:nngla:contract", candidate.parcel_candidate_id, "NG-GEO-900301", "POLYGON", "NG-CRS-EPSG4326",
        True, True, "INSIDE_SOVEREIGN_LAND", "DEFERRED_NO_REGISTERED_PARCELS", "NG-SRV-900301", "SURVEYED", "contract:survey"
    )
    assert qualify_parcel_candidate(candidate, reservation, geometry).recognition_ready
    parcel = register_qualified_parcel(candidate, reservation, geometry, effective_on=date(2026,8,17), source_reference="contract:register")
    assert parcel.parcel_id == "NV-01-001-0001"
    assert load_parcel_bootstrap() == ()
    assert artifact_rows()["parcel_bootstrap_v002"] == ()


def test_bundle17g_contract_preserves_subdivision_lineage_and_closes_without_new_public_candidate_namespace():
    lineage = promote_lineage_candidate(ParcelLineageCandidate(
        "parcel-lineage-candidate:contract", "SUBDIVISION", ("NV-01-001-0001",),
        ("NV-01-001-0002", "NV-01-001-0003"), "2026-08-17", "contract:lineage"
    ))
    assert lineage.predecessor_parcel_ids == ("NV-01-001-0001",)
    assert bundle17g_is_qualified()
