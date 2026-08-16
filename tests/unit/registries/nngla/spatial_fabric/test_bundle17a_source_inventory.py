from pathlib import Path
import csv

from registries.nngla.spatial_fabric.source_inventory import (
    BASE_FORMAT_PATH,
    BASE_NAMESPACE_PATH,
    FORMAT_EXTENSION_PATH,
    NAMESPACE_EXTENSION_PATH,
    SOURCE_ROOT,
    load_manifest,
    validate_all_sources,
    validate_identifier_extension_contracts,
    validate_governed_identifier,
)


def _rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_bundle17a_inventories_exactly_47_immutable_v001_source_csvs():
    manifest = load_manifest()
    assert len(manifest) == 47
    assert len({entry.source_path for entry in manifest}) == 47
    assert sum(entry.record_count for entry in manifest) == 7364
    assert all(entry.status == "ACTIVE_SOURCE_EVIDENCE" for entry in manifest)
    imported = [
        path for path in SOURCE_ROOT.rglob("*.csv")
        if path.parent.name in {
            "01_spatial_fabric", "02_existing_physical_world", "03_qualified_feature_candidates",
            "04_settlements_roads_administration", "05_new_waters_ocean",
        }
    ]
    assert len(imported) == 47


def test_source_contracts_verify_hash_rows_headers_and_governed_identifier_extensions():
    results = validate_all_sources()
    assert len(results) == 47
    assert all(result.contract_status == "PASS" for result in results)
    assert all(result.expected_sha256 == result.actual_sha256 for result in results)
    assert all(result.expected_row_count == result.actual_row_count for result in results)


def test_historical_namespace_and_identifier_registers_are_not_rewritten():
    base_namespaces = _rows(BASE_NAMESPACE_PATH)
    base_formats = _rows(BASE_FORMAT_PATH)
    extensions = _rows(NAMESPACE_EXTENSION_PATH)
    extension_formats = _rows(FORMAT_EXTENSION_PATH)
    assert len(base_namespaces) == 11
    assert len(base_formats) == 28
    assert len(extensions) == 32
    assert len(extension_formats) == 33
    assert not ({r["namespace_id"] for r in base_namespaces} & {r["namespace_id"] for r in extensions})
    assert not ({r["identifier_format_id"] for r in base_formats} & {r["identifier_format_id"] for r in extension_formats})
    assert validate_identifier_extension_contracts() == ()


def test_extension_contracts_cover_current_spatial_source_identifiers_but_not_arbitrary_unknown_ids():
    assert validate_governed_identifier("NG-SPT-000001")
    assert validate_governed_identifier("NG-SCELL-000001")
    assert validate_governed_identifier("NG-MGRID-01-01")
    assert validate_governed_identifier("NG-FEAT-000021")
    assert validate_governed_identifier("NG-NAM-SEA-000180")
    assert not validate_governed_identifier("NG-MADE-UP-000001")
