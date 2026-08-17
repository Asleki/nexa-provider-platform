from collections import Counter
from registries.nngla.spatial_fabric.bundle17f import (
    alignment_counts,
    derive_existing_canonical_alignment,
    remaining_noncanonical_road_candidate_ids,
)
from registries.nngla.spatial_fabric.bundle17f.contracts import CanonicalSubjectFamily


def test_locked_canonical_alignment_reconciles_exact_1284_without_renumbering():
    rows = derive_existing_canonical_alignment()
    assert len(rows) == 1284
    assert alignment_counts() == {
        "PLACE": 700,
        "ADMINISTRATIVE_AREA": 192,
        "ROAD": 350,
        "GEOGRAPHIC_FEATURE": 21,
        "EXISTING_GEOMETRY": 21,
    }
    by_family = Counter(x.object_family for x in rows)
    assert by_family[CanonicalSubjectFamily.PLACE] == 700


def test_locked_suffix_allocations_are_preserved_for_place_admin_and_first_350_roads():
    rows = derive_existing_canonical_alignment()
    places = [x for x in rows if x.object_family is CanonicalSubjectFamily.PLACE]
    admins = [x for x in rows if x.object_family is CanonicalSubjectFamily.ADMINISTRATIVE_AREA]
    roads = [x for x in rows if x.object_family is CanonicalSubjectFamily.ROAD]
    assert (places[0].canonical_id, places[-1].canonical_id) == ("NG-PLC-000001", "NG-PLC-000700")
    assert (admins[0].canonical_id, admins[-1].canonical_id) == ("NG-ADM-000001", "NG-ADM-000192")
    assert (roads[0].canonical_id, roads[-1].canonical_id) == ("NG-RD-000001", "NG-RD-000350")


def test_remaining_550_road_sources_are_explicitly_not_declared_canonical():
    remaining = remaining_noncanonical_road_candidate_ids()
    assert len(remaining) == 550
    assert remaining[0] == "NG-RD-CAND-000351"
    assert remaining[-1] == "NG-RD-CAND-000900"
    aligned = {x.candidate_id for x in derive_existing_canonical_alignment() if x.object_family is CanonicalSubjectFamily.ROAD}
    assert not aligned.intersection(remaining)
