from pathlib import Path
import json

from registries.nngla.spatial_fabric import (
    bundle17a_is_qualified,
    derive_coordinate_candidates,
    derive_coordinate_occurrences,
    derive_major_grid_topology,
    derive_reference_cell_topology,
    load_manifest,
)
from registries.nngla.spatial_fabric.source_inventory import ROOT, SOURCE_ROOT


def test_bundle17a_contract_closes_spatial_source_and_topology_foundation_without_canonical_writes():
    manifest = load_manifest()
    assert len(manifest) == 47
    assert len(derive_coordinate_occurrences()) == 5322
    assert len(derive_coordinate_candidates()) == 2411
    assert len(derive_major_grid_topology()) == 16
    assert len(derive_reference_cell_topology()) == 1104
    assert bundle17a_is_qualified()
    assert all(item.allowed_migration_action.value != "INSERT_NEW" for item in manifest)


def test_spatial_v001_evidence_is_additive_and_old_day_zero_authority_files_stay_outside_bundle17a_source_family():
    old_namespace = ROOT / "data/novegeo/nngla/foundation/source/novegeo_code_namespace.csv"
    old_formats = ROOT / "data/novegeo/nngla/foundation/source/novegeo_identifier_format_register.csv"
    assert old_namespace.is_file() and old_formats.is_file()
    assert not str(old_namespace).startswith(str(SOURCE_ROOT))
    assert not str(old_formats).startswith(str(SOURCE_ROOT))


def test_bundle17a_provenance_locks_the_exact_spatial_source_archive_and_no_postgresql_write_policy():
    path = ROOT / "data/novegeo/nngla/spatial-fabric/provenance/bundle17a_authority_source.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["source_archive"] == "NoveGeo_Spatial_Fabric_New_Waters_v001.zip"
    assert payload["source_archive_sha256"] == "145af0be26b8c8c924546e9a7686dd8a648270080160831455d68e7841d34398"
    assert payload["source_csv_count"] == 47
    assert payload["policy"] == "IMMUTABLE_V001_SOURCE_EVIDENCE_NO_POSTGRESQL_WRITES"


def test_bundle17a_does_not_add_or_modify_database_migrations():
    from hashlib import sha256

    expected = {
        "m006_07_11_nngla_cadastre_runtime.sql": "0289f9fe505cc30b52ddd284b6554d44bc049e18283004e5aea39bb595721c17",
        "m006_07_11_nngla_execution_foundation.sql": "311d349c5fb70ffae466f62281fbe226acd570ae8743d0c3e7ffc2d5640c4c3a",
        "m006_07_11_nngla_identity_places_runtime.sql": "8662852edc2c0ea782c1ab3dc141eea5faddeb82bc4bbb2e5317b61f206a72bb",
        "m006_07_11_nngla_execution_foundation_rollback.sql": "9999de9cac66c819d5cfe390d127739b345e59a8a9e10bd3b36af1e0a8f5fbba",
        "m006_07_11_nngla_geometry_roads_runtime_rollback.sql": "b62cfa2325c9eb04d87f3ca77fe809379e602ad7731df3c8aae37a39917ef14a",
        "m006_07_11_nngla_identity_places_runtime_rollback.sql": "ba692e21f950effee90dd6342e1b4d7f9b769cc603fa094f16af6cd81011b26d",
        "m006_07_11_nngla_geometry_roads_runtime.sql": "bbc847ff4f9fa0fcc73c4be0beb4a5c4bab12e0b67bb394a7f4deed47d6867e9",
        "m006_07_11_nngla_cadastre_runtime_rollback.sql": "bc0135037db52601dd4c7af58fb002051d358154dd940510ecd7cdb1bcde03fd",
    }
    migrations = sorted((ROOT / "database/migrations").glob("m006_07_11*.sql"))
    actual = {path.name: sha256(path.read_bytes()).hexdigest() for path in migrations}
    assert actual == expected
