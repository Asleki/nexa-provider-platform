from pathlib import Path

from registries.metadata import RegistryProvenance

ROOT = Path(__file__).resolve().parents[3]


def test_previous_metadata_tests_and_boundaries_remain_present():
    metadata_tests = ROOT / "tests" / "unit" / "registries" / "metadata"
    for name in (
        "test_registry_provenance.py",
        "test_registry_training_eligibility.py",
        "test_registry_data_classification.py",
        "test_registry_capability.py",
    ):
        assert (metadata_tests / name).is_file()
    registry_tests = ROOT / "tests" / "unit" / "registries"
    for name in (
        "test_m008_15_registry_metadata_boundaries.py",
        "test_m008_15_1_registry_capability_boundaries.py",
        "test_m008_15_2_data_classification_boundaries.py",
        "test_m008_15_3_training_eligibility_boundaries.py",
    ):
        assert (registry_tests / name).is_file()


def test_provenance_remains_immediate_lineage_metadata_only():
    fields = RegistryProvenance.__dataclass_fields__
    forbidden = {
        "classification_level",
        "training_status",
        "retention_mode",
        "trust_score",
        "quality_score",
        "licence_id",
        "ownership_id",
        "dataset_id",
        "migration_manifest_id",
        "source_registry_id",
        "source_record_id",
        "model_id",
        "runtime_mode",
    }
    assert forbidden.isdisjoint(fields)


def test_provenance_has_no_storage_audit_migration_or_policy_execution_imports():
    source = (ROOT / "registries" / "metadata" / "registry_provenance.py").read_text()
    forbidden = (
        "boto3",
        "sqlalchemy",
        "DatasetRepository",
        "MigrationRepository",
        "AuditRepository",
        "EventStore",
        "upload_file(",
        "migrate(",
        "verify_licence(",
        "calculate_trust(",
        "train(",
    )
    for token in forbidden:
        assert token not in source


def test_future_domains_share_the_same_provenance_contract():
    examples = (
        RegistryProvenance("institution", "hospital-registry", source_reference="BIRTH-1"),
        RegistryProvenance("institution", "school-registry", source_reference="RESULT-1"),
        RegistryProvenance("system", "nexapos-alpha", source_event_id="WEIGHT-1"),
        RegistryProvenance("import", "name-importer", source_reference="NAME-18472"),
        RegistryProvenance("derived", "ledger-read-model", source_event_id="POSTING-1"),
    )
    assert {item.source_type.value for item in examples} == {
        "institution",
        "system",
        "import",
        "derived",
    }
