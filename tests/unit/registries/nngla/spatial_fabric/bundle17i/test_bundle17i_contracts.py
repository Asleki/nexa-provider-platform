import pytest
from registries.nngla.spatial_fabric.bundle17i import (
    TitleReferenceReservation, load_title_series, title_lifecycle_rows,
)


def test_title_series_reuses_locked_ng_ttl_namespace_and_is_global_no_reuse():
    series = load_title_series()
    assert series.prefix == "NG-TTL-"
    assert series.sequence_width == 6
    assert series.allocation_scope == "SOVEREIGN_GLOBAL"
    assert series.sequence_semantics == "MONOTONIC_NO_REUSE"


def test_title_number_reservation_may_exist_without_parcel_or_holder_but_not_legal_title():
    row = TitleReferenceReservation(
        "titleres:nngla:x", "titleseries:nngla:sovereign", "NG-TTL-000001", "", "", "idempotent:1",
        "TITLE_NUMBER_RESERVED", False, "production", "test",
    )
    assert row.parcel_id == ""
    assert row.holder_reference == ""
    assert not row.legal_title_exists


def test_title_reservation_cannot_claim_issuance_or_be_consumed_by_simulation():
    with pytest.raises(ValueError):
        TitleReferenceReservation("titleres:nngla:x", "titleseries:nngla:sovereign", "NG-TTL-000001", "", "", "x", "TITLE_NUMBER_RESERVED", True, "production", "test")
    with pytest.raises(ValueError):
        TitleReferenceReservation("titleres:nngla:x", "titleseries:nngla:sovereign", "NG-TTL-000001", "", "", "x", "TITLE_NUMBER_RESERVED", False, "simulation", "test")


def test_title_lifecycle_explicitly_distinguishes_number_reservation_from_issuance():
    rows = {r["title_lifecycle_status_code"]: r for r in title_lifecycle_rows()}
    assert rows["TITLE_NUMBER_RESERVED"]["legal_title_exists"] == "false"
    assert rows["TITLE_NUMBER_RESERVED"]["parcel_required"] == "false"
    assert rows["TITLE_NUMBER_RESERVED"]["holder_reference_required"] == "false"
    assert rows["TITLE_ISSUED"]["legal_title_exists"] == "true"
