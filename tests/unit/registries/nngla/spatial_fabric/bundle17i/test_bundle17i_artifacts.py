from registries.nngla.spatial_fabric.bundle17i._shared import DAY_ZERO_TITLE_PATH, DAY_ZERO_STATE_LAND_PATH, csv_rows
from registries.nngla.spatial_fabric.bundle17i.artifacts import artifact_drift_findings, artifact_paths


def test_bundle17i_artifacts_preserve_day_zero_registers_and_create_empty_v002_operational_descendants():
    assert artifact_drift_findings() == ()
    assert csv_rows(DAY_ZERO_TITLE_PATH) == ()
    assert csv_rows(DAY_ZERO_STATE_LAND_PATH) == ()
    paths = artifact_paths()
    assert len(csv_rows(paths["title_series"])) == 1
    assert len(csv_rows(paths["title_lifecycle"])) == 9
    for key in ("title_reservations","title_issuance_candidates","state_land_candidates","title_bootstrap_v002","state_land_bootstrap_v002"):
        assert csv_rows(paths[key]) == ()
