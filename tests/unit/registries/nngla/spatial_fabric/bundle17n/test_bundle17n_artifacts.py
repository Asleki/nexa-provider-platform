from registries.nngla.spatial_fabric.bundle17n.artifacts import artifact_paths
def test_all_governed_artifacts_exist():
    paths=artifact_paths()
    assert {"command_catalogue","command_authorization","bulk_policy","idempotency_policy","validation_rules","foundation_authority_matrix","schema"}==set(paths)
    assert all(p.exists() for p in paths.values())
