from registries.nngla.migration_architecture.limits import (
    IDENTIFIER_LIMIT,
    LONGITUDE_RANGE,
    LATITUDE_RANGE,
    MAX_BATCH_SIZE,
    validate_batch_limit,
)
from registries.nngla.migration_architecture.plans import get_plan
from registries.nngla.migration_architecture.qualification import QualificationEngine, QualificationOutcome
from registries.nngla.migration_architecture.source_catalogue import load_source


def test_bundle16b_limit_contracts_match_spatial_defensive_ranges_and_name_authority_precedent():
    assert LONGITUDE_RANGE.validate(-180) == ()
    assert LONGITUDE_RANGE.validate(180) == ()
    assert LATITUDE_RANGE.validate(-90) == ()
    assert LATITUDE_RANGE.validate(90) == ()
    assert LONGITUDE_RANGE.validate(180.01)
    assert LATITUDE_RANGE.validate(-90.01)
    assert IDENTIFIER_LIMIT.max_length == 256
    assert MAX_BATCH_SIZE == 10_000


def test_batch_limit_rejects_zero_negative_and_over_10000():
    assert validate_batch_limit(1) == ()
    assert validate_batch_limit(10_000) == ()
    assert validate_batch_limit(0)
    assert validate_batch_limit(-1)
    assert validate_batch_limit(10_001)


def test_current_place_city_record_qualifies_and_receives_canonical_place_id():
    snapshot = load_source("places")
    record = next(r for r in snapshot.records if r.payload["place_type_code"] == "CITY")
    result = QualificationEngine().qualify(get_plan("places:city"), snapshot, record)
    assert result.outcome is QualificationOutcome.QUALIFIED
    assert result.proposed_canonical_id == "NG-PLC-000001"
    assert result.findings == ()


def test_current_road_record_qualifies_against_controlled_road_class():
    snapshot = load_source("roads")
    result = QualificationEngine().qualify(get_plan("roads"), snapshot, snapshot.records[0])
    assert result.outcome is QualificationOutcome.QUALIFIED
    assert result.proposed_canonical_id == "NG-RD-000001"


def test_current_geometry_record_qualifies_with_epsg4326_checksum_and_existing_source_path():
    snapshot = load_source("geometry")
    result = QualificationEngine().qualify(get_plan("geometry"), snapshot, snapshot.records[0])
    assert result.outcome is QualificationOutcome.QUALIFIED
    assert result.proposed_canonical_id == "NG-GEO-000001"


def test_sovereign_boundary_qualifies_as_multipolygon_version_two_without_canonical_object_promotion():
    snapshot = load_source("sovereign-boundary")
    assert len(snapshot.records) == 1
    result = QualificationEngine().qualify(get_plan("sovereign-boundary"), snapshot, snapshot.records[0])
    assert result.outcome is QualificationOutcome.QUALIFIED
    assert result.proposed_canonical_id is None


def test_governed_empty_sources_are_present_and_not_missing_files():
    for key in ("survey-control", "addresses", "parcels", "titles", "state-land"):
        snapshot = load_source(key)
        assert snapshot.governed_empty is True
        assert snapshot.records == ()
        assert snapshot.byte_size > 0
