from collections import Counter

from registries.nngla.spatial_fabric.coordinate_occurrences import (
    candidate_identity,
    derive_coordinate_candidates,
    derive_coordinate_occurrences,
    occurrence_crosswalk_rows,
)


def test_all_semantic_coordinate_occurrences_are_extracted_without_treating_extents_as_points():
    occurrences = derive_coordinate_occurrences()
    assert len(occurrences) == 5322
    by_file = Counter(item.source_file_id for item in occurrences)
    # Major grid boxes contain bounds but no semantic point pair and therefore create no occurrences.
    assert len(by_file) < 47
    assert all(item.source_longitude_text and item.source_latitude_text for item in occurrences)


def test_exact_numeric_locations_deduplicate_to_2411_deterministic_candidates():
    occurrences = derive_coordinate_occurrences()
    candidates = derive_coordinate_candidates(occurrences)
    reversed_candidates = derive_coordinate_candidates(tuple(reversed(occurrences)))
    assert len(candidates) == 2411
    assert [(c.coordinate_candidate_id, c.canonical_longitude, c.canonical_latitude) for c in candidates] == [
        (c.coordinate_candidate_id, c.canonical_longitude, c.canonical_latitude) for c in reversed_candidates
    ]
    assert sum(c.occurrence_count for c in candidates) == 5322
    assert all(c.canonicalization_status == "CANDIDATE_ONLY_NOT_PERSISTED" for c in candidates)


def test_occurrence_crosswalk_reuses_one_candidate_for_repeated_numeric_coordinates():
    occurrences = derive_coordinate_occurrences()
    crosswalk = occurrence_crosswalk_rows(occurrences)
    assert len(crosswalk) == 5322
    assert len({row["coordinate_occurrence_id"] for row in crosswalk}) == 5322
    assert len({row["coordinate_candidate_id"] for row in crosswalk}) == 2411
    first = occurrences[0]
    assert candidate_identity(first.source_longitude_numeric, first.source_latitude_numeric) == crosswalk[0]["coordinate_candidate_id"]
