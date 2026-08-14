from pathlib import Path

from registries.nngla.bundle15d_qualification import qualify_bundle15d
from registries.nngla.sovereign_readiness import qualify_sovereign_spatial_readiness

ROOT = Path(__file__).resolve().parents[4]


def test_p006_7_10_sovereign_spatial_stack_qualifies_without_claiming_full_population():
    receipt = qualify_sovereign_spatial_readiness(ROOT)
    assert receipt.status == "QUALIFIED"
    assert receipt.findings == ()
    assert receipt.authority_readiness == "READY"
    assert receipt.read_model_readiness == "READY"
    assert receipt.publication_readiness == "READY_POLICY_NO_ELIGIBLE_DOMAIN_RECORDS"
    assert receipt.place_population_state == "SOURCE_READY_NOT_MIGRATED"
    assert receipt.road_population_state == "SOURCE_READY_NOT_MIGRATED"
    assert receipt.address_population_state == "EMPTY_DAY_ZERO"
    assert receipt.parcel_population_state == "EMPTY_DAY_ZERO"
    assert receipt.title_population_state == "EMPTY_DAY_ZERO"
    assert receipt.state_land_population_state == "EMPTY_DAY_ZERO"


def test_p006_7_10_preserves_truth_that_live_database_migration_is_not_executed():
    receipt = qualify_sovereign_spatial_readiness(ROOT)
    assert receipt.live_database_migration_status == "NOT_EXECUTED"
    assert receipt.pwa_consumer_boundary == "READ_ONLY_API_NO_DATABASE_AUTHORITY"


def test_bundle15d_qualification_preserves_day_zero_publication_counts():
    receipt = qualify_bundle15d(ROOT)
    assert receipt.status == "QUALIFIED"
    assert receipt.findings == ()
    assert receipt.source_place_count == 700
    assert receipt.source_road_count == 900
    assert receipt.canonical_place_count == 0
    assert receipt.canonical_road_count == 0
    assert receipt.published_place_count == 0
    assert receipt.published_road_count == 0
    assert receipt.published_address_count == 0
    assert receipt.published_parcel_count == 0
    assert receipt.sovereign_readiness_status == "QUALIFIED"


def test_bundle15d_semantic_checksum_is_repeatable():
    first = qualify_bundle15d(ROOT)
    second = qualify_bundle15d(ROOT)
    assert first.semantic_checksum == second.semantic_checksum
