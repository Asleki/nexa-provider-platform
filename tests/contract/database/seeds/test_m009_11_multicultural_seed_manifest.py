from ._seed_manifest_test_support import (
    assert_common_manifest_contract,
    assert_file_integrity,
    load_manifest,
)


def test_multicultural_manifest_preserves_explicit_semantic_roles_and_unicode():
    manifest = load_manifest("name_catalogue/multicultural/manifest.json")
    assert_common_manifest_contract(manifest)
    assert manifest["dataset_id"] == "dataset.novegeo.name_catalogue.multicultural.v001"
    entries = {entry["file_id"]: entry for entry in manifest["files"]}
    assert entries["file.novegeo.multicultural.first_names.v001"]["target_name_kind"] == "first_name"
    assert entries["file.novegeo.multicultural.accented_first_names.v001"]["target_name_kind"] == "first_name"
    assert entries["file.novegeo.multicultural.family_names.v001"]["target_name_kind"] == "surname"
    assert entries["file.novegeo.multicultural.accented_family_names.v001"]["target_name_kind"] == "surname"
    assert manifest["activation"]["preserve_unicode"] is True
    for entry in manifest["files"]:
        assert_file_integrity(entry)


def test_accented_datasets_really_contain_non_ascii_canonical_values():
    manifest = load_manifest("name_catalogue/multicultural/manifest.json")
    entries = {entry["file_id"]: entry for entry in manifest["files"]}
    first_rows = assert_file_integrity(entries["file.novegeo.multicultural.accented_first_names.v001"])
    family_rows = assert_file_integrity(entries["file.novegeo.multicultural.accented_family_names.v001"])
    assert any(not row["first_name"].isascii() for row in first_rows)
    assert any(not row["second name"].isascii() for row in family_rows)
