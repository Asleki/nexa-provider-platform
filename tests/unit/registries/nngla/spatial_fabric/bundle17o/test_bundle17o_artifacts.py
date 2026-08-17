from registries.nngla.spatial_fabric.bundle17o.artifacts import artifact_paths
def test_all_required_artifacts_exist():
    p=artifact_paths()
    assert {"query_catalogue","result_contracts","read_models","geocoding_rules","cross_registry","schema"}==set(p)
    assert all(x.exists() for x in p.values())
