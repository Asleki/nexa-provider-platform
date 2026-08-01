from ._seed_manifest_test_support import (
    assert_common_manifest_contract,
    assert_file_integrity,
    load_manifest,
)


def test_novegeo_manifest_integrity_and_domain_mappings():
    manifest = load_manifest("name_catalogue/novegeo/manifest.json")
    assert_common_manifest_contract(manifest)
    assert manifest["dataset_id"] == "dataset.novegeo.name_catalogue.native.v001"
    entries = {entry["file_id"]: entry for entry in manifest["files"]}
    assert entries["file.novegeo.native.first_names.v001"]["target_name_kind"] == "first_name"
    assert entries["file.novegeo.native.second_names.v001"]["target_name_kind"] == "middle_name"
    assert entries["file.novegeo.native.surnames.v001"]["target_name_kind"] == "surname"
    assert entries["file.novegeo.native.tribes.v001"]["import_enabled"] is False
    for entry in manifest["files"]:
        assert_file_integrity(entry)


def test_every_novegeo_surname_tribe_reference_resolves():
    manifest = load_manifest("name_catalogue/novegeo/manifest.json")
    entries = {entry["file_id"]: entry for entry in manifest["files"]}
    surnames = assert_file_integrity(entries["file.novegeo.native.surnames.v001"])
    tribes = assert_file_integrity(entries["file.novegeo.native.tribes.v001"])
    tribe_ids = {row["id"] for row in tribes}
    assert tribe_ids
    assert all(row["tribe"] in tribe_ids for row in surnames)
    relationship = manifest["relationships"][0]
    assert relationship["validation"] == "required"
    assert relationship["future_registry_binding"] == "reserved"
