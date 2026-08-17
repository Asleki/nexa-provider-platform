from registries.nngla.spatial_fabric.bundle17g import artifact_drift_findings, artifact_paths
from registries.nngla.spatial_fabric.bundle17g.artifacts import artifact_rows
from registries.nngla.spatial_fabric.bundle17g._shared import DAY_ZERO_PARCEL_PATH, csv_rows


def test_bundle17g_creates_required_versioned_contracts_without_fabricated_parcels():
    paths = artifact_paths()
    assert len(paths) == 7
    assert paths["parcel_bootstrap_v002"].name == "parcel_bootstrap_v002.csv"
    rows = artifact_rows()
    assert len(rows["cadastral_series_definitions"]) == 1
    assert len(rows["parcel_lifecycle_status_codes"]) == 7
    for key in ("parcel_candidates", "parcel_reservations", "parcel_geometry_candidates", "parcel_lineage_candidates", "parcel_bootstrap_v002"):
        assert rows[key] == ()


def test_historical_day_zero_parcel_register_stays_empty_and_new_artifacts_have_no_drift():
    assert csv_rows(DAY_ZERO_PARCEL_PATH) == ()
    assert artifact_drift_findings() == ()
