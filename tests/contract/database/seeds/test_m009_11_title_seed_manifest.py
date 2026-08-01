from ._seed_manifest_test_support import (
    assert_common_manifest_contract,
    assert_file_integrity,
    load_manifest,
)


def test_title_manifest_reserves_a_separate_catalogue_and_blocks_name_import():
    manifest = load_manifest("title_catalogue/manifest.json")
    assert_common_manifest_contract(manifest)
    assert manifest["dataset_id"] == "dataset.novegeo.title_catalogue.v001"
    entry = manifest["files"][0]
    assert entry["record_role"] == "title_reference"
    assert entry["import_enabled"] is False
    assert "target_name_kind" not in entry
    activation = manifest["activation"]
    assert activation["canonical_name_import_allowed"] is False
    assert activation["target_contract"] == "reserved_title_catalogue"
    assert activation["title_domain_model_required_before_activation"] is True
    assert_file_integrity(entry)
