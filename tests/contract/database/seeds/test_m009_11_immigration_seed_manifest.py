from ._seed_manifest_test_support import (
    assert_common_manifest_contract,
    assert_file_integrity,
    load_manifest,
)


def test_immigration_manifest_models_complete_pairs_without_foreign_country_simulation():
    manifest = load_manifest("name_catalogue/immigration/manifest.json")
    assert_common_manifest_contract(manifest)
    assert manifest["dataset_id"] == "dataset.novegeo.name_catalogue.immigration.v001"
    entry = manifest["files"][0]
    assert entry["record_role"] == "paired_full_name_source"
    assert entry["column_mappings"]["first_name"] == "first_component.raw_name_value"
    assert entry["column_mappings"]["second_name"] == "surname_component.raw_name_value"
    assert manifest["activation"]["atomic_component_import_supported"] is True
    assert manifest["activation"]["formal_pair_relationship_import_supported"] is False
    assert manifest["activation"]["foreign_country_simulation_required"] is False
    assert_file_integrity(entry)


def test_pair_relationship_is_reserved_without_changing_canonical_name_identity():
    manifest = load_manifest("name_catalogue/immigration/manifest.json")
    relationship = manifest["relationships"][0]
    assert relationship["semantic_roles"] == ["first_name", "surname"]
    assert relationship["pairing_relationship_persistence"] == "deferred"
    assert relationship["future_pair_id_namespace"] == "namepair:"
