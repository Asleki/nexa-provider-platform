import pytest
from registries.nngla.spatial_fabric.bundle17g import CadastralSeriesDefinition, MemoryParcelReferenceAllocator, form_parcel_candidate


def test_parcel_candidate_identity_is_private_and_physical_ground_stays_distinct():
    candidate = form_parcel_candidate(
        physical_ground_reference="NG-SPT-000001", proposed_land_use_code="AGRICULTURAL", source_reference="test:ground"
    )
    assert candidate.parcel_candidate_id.startswith("parcelcand:nngla:")
    assert not candidate.parcel_candidate_id.startswith("NV-")
    assert candidate.physical_ground_reference == "NG-SPT-000001"


def test_reference_reservation_creates_sovereign_number_without_claiming_registered_parcel():
    candidate = form_parcel_candidate(
        physical_ground_reference="NG-SPT-000001", proposed_land_use_code="AGRICULTURAL", source_reference="test:ground"
    )
    allocation = MemoryParcelReferenceAllocator(start_sequence=8890).reserve(candidate, CadastralSeriesDefinition("12", "004"))
    assert allocation.parcel_id == "NV-12-004-8890"
    assert allocation.legal_effect is False
    assert allocation.canonical_parcel_registered is False


def test_simulation_cannot_independently_consume_sovereign_parcel_number():
    candidate = form_parcel_candidate(
        physical_ground_reference="NG-SPT-000002", proposed_land_use_code="RESIDENTIAL", source_reference="test:ground"
    )
    with pytest.raises(ValueError):
        MemoryParcelReferenceAllocator().reserve(candidate, CadastralSeriesDefinition("12", "004"), authority_runtime_mode="simulation")


def test_allocator_is_idempotent_per_candidate_and_skips_occupied_numbers():
    series = CadastralSeriesDefinition("12", "004")
    a = form_parcel_candidate(physical_ground_reference="NG-SPT-000010", proposed_land_use_code="AGRICULTURAL", source_reference="test:a")
    b = form_parcel_candidate(physical_ground_reference="NG-SPT-000011", proposed_land_use_code="AGRICULTURAL", source_reference="test:b")
    allocator = MemoryParcelReferenceAllocator(occupied_parcel_ids={"NV-12-004-0001"})
    ra = allocator.reserve(a, series)
    assert ra.parcel_id == "NV-12-004-0002"
    assert allocator.reserve(a, series) == ra
    rb = allocator.reserve(b, series)
    assert rb.parcel_id == "NV-12-004-0003"
