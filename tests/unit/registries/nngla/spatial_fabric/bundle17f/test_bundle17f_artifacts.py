from registries.nngla.spatial_fabric.bundle17f import artifact_drift_findings, artifact_paths
from registries.nngla.spatial_fabric.bundle17f.artifacts import artifact_rows


def test_bundle17f_artifact_contract_has_four_new_companion_files():
    paths = artifact_paths()
    assert set(paths) == {"canonical_alignment", "association_candidates", "traversal_qualification", "association_preconditions"}
    assert paths["canonical_alignment"].name == "novegeo_existing_canonical_alignment_v002.csv"


def test_bundle17f_materialized_artifacts_match_deterministic_derivation():
    rows = artifact_rows()
    assert len(rows["canonical_alignment"]) == 1284
    assert len(rows["association_candidates"]) == 1263
    assert len(rows["traversal_qualification"]) == 21
    assert len(rows["association_preconditions"]) == 1263
    assert artifact_drift_findings() == ()
