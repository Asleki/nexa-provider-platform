import pytest
from registries.nngla.spatial_fabric.bundle17g import (
    CadastralSeriesDefinition,
    ParcelLifecycleStage,
    advance_stage,
    cadastral_series_policy_rows,
    load_policy,
    parcel_lifecycle_rows,
)


def test_cadastral_series_policy_reuses_locked_nv_format_without_admin_dependency():
    policy = load_policy()
    assert policy.parcel_id_pattern == r"^NV-\d{2}-\d{3}-\d{4,}$"
    assert policy.administrative_area_dependency == "INDEPENDENT_OF_ADMINISTRATIVE_BOUNDARIES"
    assert cadastral_series_policy_rows()[0]["sequence_semantics"] == "MONOTONIC_SERIES_LOCAL_NO_REUSE"


def test_runtime_series_definition_is_cadastral_not_administrative_identity():
    series = CadastralSeriesDefinition("12", "004")
    assert series.parcel_prefix == "NV-12-004"
    with pytest.raises(ValueError): CadastralSeriesDefinition("NGR-01", "004")


def test_lifecycle_separates_physical_ground_candidate_reservation_and_registration():
    rows = parcel_lifecycle_rows()
    assert [r["lifecycle_status_code"] for r in rows] == [x.value for x in ParcelLifecycleStage]
    assert rows[0]["canonical_parcel_exists"] == "false"
    assert rows[2]["parcel_reference_required"] == "true"
    assert rows[-1]["canonical_parcel_exists"] == "true"
    assert advance_stage(ParcelLifecycleStage.PHYSICAL_GROUND, ParcelLifecycleStage.PARCEL_CANDIDATE) is ParcelLifecycleStage.PARCEL_CANDIDATE
    with pytest.raises(ValueError): advance_stage(ParcelLifecycleStage.PARCEL_CANDIDATE, ParcelLifecycleStage.REGISTERED)
