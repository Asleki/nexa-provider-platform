from registries.nngla.migration_ready.batching import build_fixed_windows, build_profile_windows, ordered_candidate_ids
from registries.nngla.migration_ready.catalogue import get_batch_profile
from registries.nngla.spatial_fabric.bundle17e.canonical import canonical_by_candidate


def test_locked_candidates_order_by_canonical_identity_and_profile():
    ids = ordered_candidate_ids(canonical_by_candidate())
    assert len(ids) == 2411
    windows = build_profile_windows(ids, get_batch_profile("initial-spatial-2411"))
    assert [w.selected_count for w in windows] == [11, 800, 800, 800]
    assert tuple(x for w in windows for x in w.candidate_ids) == ids


def test_fixed_batching_supports_one_shot_and_smaller_network_windows():
    ids = ordered_candidate_ids(canonical_by_candidate())
    assert [w.selected_count for w in build_fixed_windows(ids, 2411)] == [2411]
    windows = build_fixed_windows(ids, 500)
    assert [w.selected_count for w in windows] == [500, 500, 500, 500, 411]
