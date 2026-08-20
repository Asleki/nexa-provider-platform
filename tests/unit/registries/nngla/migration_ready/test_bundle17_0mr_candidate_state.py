from registries.nngla.migration_ready.candidate_state import assess_candidate_state
from registries.nngla.migration_ready.catalogue import ROOT


def test_candidate_boundaries_prevent_accidental_canonical_promotion():
    report = assess_candidate_state(ROOT)
    assert report.passed
    assert report.road_candidate_count == 900
    assert report.locked_road_count == 350
    assert report.candidate_only_road_count == 550
    assert report.feature_reuse_count == 21
    assert report.feature_pending_recognition_count == 5
    assert report.feature_deferred_count == 11
