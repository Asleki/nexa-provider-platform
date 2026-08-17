from pathlib import Path

from registries.nngla.spatial_fabric.bundle17c.artifacts import artifact_drift_findings, artifact_paths, artifact_rows, materialize_artifacts


def test_bundle17c_artifact_contract_has_five_required_files():
    paths = artifact_paths()
    assert set(paths) == {"relationship_types", "occupancy", "compatibility_rules", "conflict_rule_sets", "conflict_results"}
    assert {path.name for path in paths.values()} == {
        "novegeo_spatial_relationship_type_codes_v001.csv",
        "novegeo_spatial_occupancy_relationships_v002.csv",
        "novegeo_feature_compatibility_rules_v001.csv",
        "novegeo_spatial_conflict_rule_sets_v001.csv",
        "novegeo_spatial_conflict_qualification_results_v001.csv",
    }


def test_bundle17c_materialization_is_deterministic(tmp_path: Path):
    paths = materialize_artifacts(tmp_path)
    assert len(paths) == 5
    assert all(path.is_file() for path in paths)
    assert artifact_drift_findings(tmp_path) == ()
    rows = artifact_rows()
    assert len(rows["relationship_types"]) == 10
    assert len(rows["occupancy"]) == 34
    assert len(rows["compatibility_rules"]) == 16
    assert len(rows["conflict_rule_sets"]) == 5
    assert len(rows["conflict_results"]) == 34
