from registries.nngla.spatial_fabric.bundle17d import load_marine_sources, marine_source_findings


def test_bundle17d_preserves_exact_eleven_file_new_waters_source_shape():
    data = load_marine_sources()
    assert len(data) == 11
    assert {name: len(rows) for name, rows in data.items()} == {
        "novegeo_marine_waterbodies_v001.csv": 1,
        "novegeo_marine_waterbody_vertices_v001.csv": 0,
        "novegeo_marine_coastal_interfaces_v001.csv": 23,
        "novegeo_marine_route_anchor_points_v001.csv": 10,
        "novegeo_sea_route_candidates_v001.csv": 5,
        "novegeo_sea_route_vertices_v001.csv": 25,
        "novegeo_sea_route_derivation_crosswalk_v001.csv": 25,
        "novegeo_island_mainland_connections_v001.csv": 5,
        "novegeo_marine_route_validation_v001.csv": 5,
        "novegeo_island_physical_state_v001.csv": 5,
        "novegeo_sea_route_name_catalogue_v001.csv": 180,
    }
    assert marine_source_findings() == ()


def test_bundle17d_does_not_invent_outer_marine_envelope_or_assign_route_names():
    data = load_marine_sources()
    water = data["novegeo_marine_waterbodies_v001.csv"][0]
    assert data["novegeo_marine_waterbody_vertices_v001.csv"] == ()
    assert water["geometry_status"] == "COASTAL_INTERFACES_DEFINED_OUTER_MARINE_ENVELOPE_NOT_PRESENT_IN_REPOSITORY"
    assert water["sovereignty_claim_status"] == "NOT_ASSERTED_BY_THIS_RECORD"
    routes = data["novegeo_sea_route_candidates_v001.csv"]
    assert all(not row["route_name_id"] and not row["canonical_route_name"] and row["naming_status"] == "UNNAMED" for row in routes)
