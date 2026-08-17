from pathlib import Path

from registries.nngla.spatial_fabric.bundle17d.artifacts import artifact_drift_findings, artifact_paths, artifact_rows, materialize_artifacts


def test_bundle17d_has_exact_three_required_new_artifacts():
    paths = artifact_paths()
    assert set(paths) == {"feature_type_extensions", "marine_route_types", "marine_qualification"}
    assert {path.name for path in paths.values()} == {
        "novegeo_feature_type_code_extensions_v001.csv",
        "novegeo_marine_route_type_codes_v001.csv",
        "novegeo_marine_spatial_qualification_results_v001.csv",
    }


def test_bundle17d_materialization_is_deterministic(tmp_path: Path):
    paths = materialize_artifacts(tmp_path)
    assert len(paths) == 3
    assert all(path.is_file() for path in paths)
    assert artifact_drift_findings(tmp_path) == ()
    rows = artifact_rows()
    assert len(rows["feature_type_extensions"]) == 5
    assert len(rows["marine_route_types"]) == 1
    assert len(rows["marine_qualification"]) == 49
