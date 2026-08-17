from datetime import date
import pytest
from registries.nngla.spatial_fabric.bundle17i import form_state_land_candidate, recognize_state_land_candidate


def test_state_land_candidate_does_not_claim_legal_state_land_existence():
    candidate = form_state_land_candidate(parcel_id="NV-01-001-0001", state_land_category_code="GENERAL_STATE_LAND", runtime_mode="simulation", source_reference="test")
    assert candidate.candidate_status == "CANDIDATE"
    assert not candidate.legal_state_land_exists
    with pytest.raises(ValueError):
        recognize_state_land_candidate(candidate, effective_on=date(2026,8,17), source_reference="test:recognize")


def test_production_state_land_candidate_can_be_promoted_without_changing_parcel_identity():
    candidate = form_state_land_candidate(parcel_id="NV-01-001-0002", state_land_category_code="GENERAL_STATE_LAND", runtime_mode="production", source_reference="test")
    record = recognize_state_land_candidate(candidate, effective_on=date(2026,8,17), source_reference="test:recognize")
    assert record.parcel_id == candidate.parcel_id
    assert record.state_land_category_code == candidate.state_land_category_code
