from collections import Counter, defaultdict

from registries.nngla.spatial_fabric.bundle17d import derive_marine_spatial_qualification_results, load_marine_sources


def test_bundle17d_qualifies_49_marine_subjects_with_only_the_ocean_geometry_limitation_deferred():
    rows = derive_marine_spatial_qualification_results()
    assert len(rows) == 49
    assert Counter(row.subject_type.value for row in rows) == Counter({
        "MARINE_WATERBODY": 1,
        "COASTAL_INTERFACE": 23,
        "MARINE_ANCHOR": 10,
        "SEA_ROUTE": 5,
        "MARINE_CONNECTION": 5,
        "ISLAND_PHYSICAL_STATE": 5,
    })
    assert Counter(row.qualification_status for row in rows) == Counter({"PASS": 48, "PASS_WITH_KNOWN_GEOMETRY_LIMITATION": 1})
    water = next(row for row in rows if row.subject_type.value == "MARINE_WATERBODY")
    assert "OUTER_MARINE_ENVELOPE_NOT_IN_REPOSITORY" in water.findings
    assert water.sovereignty_assertion_status == "NOT_ASSERTED_BY_THIS_RECORD"


def test_bundle17d_five_routes_have_boundary_endpoints_and_marine_interiors_from_bundle17b_evidence():
    rows = [row for row in derive_marine_spatial_qualification_results() if row.subject_type.value == "SEA_ROUTE"]
    assert len(rows) == 5
    assert all(row.coordinate_qualification_status == "PASS" for row in rows)
    assert all(row.containment_context == "BOUNDARY_TO_MARINE_INTERIOR_TO_BOUNDARY" for row in rows)
    assert all(row.land_overlap_status == "ZERO_LAND_OVERLAP" for row in rows)
    assert all(row.naming_status == "UNNAMED" for row in rows)


def test_bundle17d_island_route_connection_chain_is_one_to_one():
    data = load_marine_sources()
    routes = data["novegeo_sea_route_candidates_v001.csv"]
    connections = data["novegeo_island_mainland_connections_v001.csv"]
    states = data["novegeo_island_physical_state_v001.csv"]
    assert len({row["destination_island_candidate_id"] for row in routes}) == 5
    assert len({row["island_candidate_id"] for row in connections}) == 5
    assert len({row["island_candidate_id"] for row in states}) == 5
    assert {row["destination_island_candidate_id"] for row in routes} == {row["island_candidate_id"] for row in connections} == {row["island_candidate_id"] for row in states}
