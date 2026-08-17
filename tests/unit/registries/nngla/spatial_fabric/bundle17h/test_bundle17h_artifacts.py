from registries.nngla.spatial_fabric.bundle17h._shared import DAY_ZERO_ADDRESS_PATH, csv_rows, csv_header
from registries.nngla.spatial_fabric.bundle17h.artifacts import artifact_drift_findings, artifact_paths


def test_bundle17h_artifacts_are_materialized_and_day_zero_address_register_stays_immutable():
    paths = artifact_paths()
    assert artifact_drift_findings() == ()
    assert csv_rows(DAY_ZERO_ADDRESS_PATH) == ()
    assert len(csv_rows(paths["road_segments"])) == 350
    assert len(csv_rows(paths["house_crosswalk"])) == 120
    assert len(csv_rows(paths["house_site_requirements"])) == 120
    for key in ("road_frontages","address_series","address_reservations","address_reference_v002","site_candidates","structure_site_references","site_address_assignments"):
        assert csv_rows(paths[key]) == ()


def test_address_v002_uses_road_id_and_never_revives_street_id():
    header = csv_header(artifact_paths()["address_reference_v002"])
    assert "road_id" in header
    assert "street_id" not in header
