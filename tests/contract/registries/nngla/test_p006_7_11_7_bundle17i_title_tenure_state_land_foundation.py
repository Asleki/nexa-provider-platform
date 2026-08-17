from datetime import date
from registries.nngla.spatial_fabric.bundle17i import (
    MemoryTitleReferenceAllocator, bundle17i_is_qualified, form_state_land_candidate,
    form_title_issuance_candidate, issue_qualified_title, load_schema17i_sql,
    load_title_series, qualify_schema17i_sql, qualify_title_issuance,
)
from registries.nngla.spatial_fabric.bundle17i._shared import DAY_ZERO_TITLE_PATH, DAY_ZERO_STATE_LAND_PATH, csv_rows
from registries.nngla.spatial_fabric.bundle17i.artifacts import artifact_paths


def test_bundle17i_contract_reserves_title_number_before_parcel_holder_or_legal_title_exists():
    reservation = MemoryTitleReferenceAllocator().reserve(load_title_series(), idempotency_key="contract:reserve")
    assert reservation.reserved_title_id == "NG-TTL-000001"
    assert reservation.parcel_id == ""
    assert reservation.holder_reference == ""
    assert reservation.legal_title_exists is False


def test_bundle17i_contract_issuance_reuses_reserved_identity_and_keeps_v001_v002_registers_unfabricated():
    reservation = MemoryTitleReferenceAllocator().reserve(load_title_series(), idempotency_key="contract:issue")
    candidate = form_title_issuance_candidate(
        reservation, parcel_id="NV-01-001-0001", title_type_code="FREEHOLD_TITLE", tenure_type_code="FREEHOLD",
        holder_reference="citizen:contract:1", source_reference="contract:issue",
    )
    assert qualify_title_issuance(reservation, candidate).issuance_ready
    title = issue_qualified_title(reservation, candidate, effective_on=date(2026,8,17), source_reference="contract:issued")
    assert title.title_id == reservation.reserved_title_id
    assert csv_rows(DAY_ZERO_TITLE_PATH) == ()
    assert csv_rows(DAY_ZERO_STATE_LAND_PATH) == ()
    assert csv_rows(artifact_paths()["title_bootstrap_v002"]) == ()
    assert csv_rows(artifact_paths()["state_land_bootstrap_v002"]) == ()


def test_bundle17i_contract_state_land_candidate_is_not_legal_effect_and_postgresql_contract_is_additive():
    candidate = form_state_land_candidate(parcel_id="NV-01-001-0002", state_land_category_code="GENERAL_STATE_LAND", runtime_mode="simulation", source_reference="contract:state")
    assert candidate.legal_state_land_exists is False
    assert qualify_schema17i_sql(load_schema17i_sql()) == ()
    assert bundle17i_is_qualified()
