from pathlib import Path
from registries.nngla.migration_source import *
from registries.nngla.source_dataset import DatasetClass,MigrationEligibility,DataClassification


def test_governed_snapshot_contains_real_populated_and_empty_candidate_registers():
    manifest=load_manifest()
    by_path={x.relative_path:x for x in manifest}
    assert by_path["06_roads_addresses/road_reference_candidates.csv"].row_count==900
    assert by_path["06_roads_addresses/address_reference_candidates.csv"].dataset_class is DatasetClass.REAL_EMPTY_GOVERNED_REGISTER
    assert by_path["07_land/parcel_bootstrap.csv"].migration_eligibility is MigrationEligibility.DEFERRED_SPATIAL_OR_LEGAL
    assert len(load_candidate_rows("05_geographic_candidates/geographic_feature_candidates.csv"))==21
    assert len(load_candidate_rows("09_quarantine/invalid_geographic_feature_candidates.csv"))==0


def test_crs_geometry_classification_and_evidence_are_preserved():
    crs=load_crs_rows(); geometry=load_geometry_type_rows(); classes=load_data_classifications()
    assert crs[0]["crs_code"]=="NG-CRS-EPSG4326" and crs[0]["authority_code"]=="4326"
    assert {x["geometry_type_code"] for x in geometry}=={"POINT","MULTIPOINT","LINESTRING","MULTILINESTRING","POLYGON","MULTIPOLYGON"}
    assert DataClassification.SECURITY_SENSITIVE in classes
    evidence=load_validation_evidence()
    assert any(x.file_path=="06_roads_addresses/road_reference_candidates.csv" and x.row_count==900 and x.result=="PASS" for x in evidence)
