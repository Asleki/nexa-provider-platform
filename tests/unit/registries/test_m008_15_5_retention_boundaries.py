from datetime import timedelta
from pathlib import Path

from registries.metadata import RegistryRetention

ROOT = Path(__file__).resolve().parents[3]


def test_original_and_previous_metadata_tests_remain_present():
    metadata_tests = ROOT / "tests" / "unit" / "registries" / "metadata"
    for name in (
        "test_registry_retention.py",
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
        "test_m008_15_4_provenance_boundaries.py",
    ):
        assert (registry_tests / name).is_file()


def test_retention_remains_declaration_metadata_only():
    fields = RegistryRetention.__dataclass_fields__
    forbidden = {
        "runtime_mode",
        "registry_id",
        "record_id",
        "event_id",
        "archive_id",
        "hold_id",
        "dataset_id",
        "migration_manifest_id",
        "storage_path",
        "database_table",
        "cloud_provider",
        "deletion_status",
        "archive_status",
    }
    assert forbidden.isdisjoint(fields)


def test_retention_has_no_storage_deletion_archive_or_legal_execution_imports():
    source = (ROOT / "registries" / "metadata" / "registry_retention.py").read_text()
    forbidden = (
        "boto3",
        "sqlalchemy",
        "os.remove(",
        "shutil.rmtree(",
        "unlink(",
        "delete_record(",
        "archive_record(",
        "release_legal_hold(",
        "EventStore",
        "ArchiveRepository",
        "DeletionRepository",
    )
    for token in forbidden:
        assert token not in source


def test_future_domains_share_one_storage_neutral_retention_contract():
    examples = (
        RegistryRetention("permanent", "Country history"),
        RegistryRetention("permanent", "Citizen birth history"),
        RegistryRetention(
            "event_triggered",
            "Bank evidence",
            trigger_event="ACCOUNT.CLOSED",
            retention_period=timedelta(days=365 * 7),
        ),
        RegistryRetention(
            "fixed_duration",
            "NexaPOS local draft",
            retention_period=timedelta(days=30),
            deletion_permitted=True,
        ),
        RegistryRetention(
            "policy_review_required",
            "Healthcare policy review",
            policy_reference="HEALTH-POLICY-1",
        ),
    )
    assert [item.mode.value for item in examples] == [
        "permanent",
        "permanent",
        "event_triggered",
        "fixed_duration",
        "policy_review_required",
    ]
