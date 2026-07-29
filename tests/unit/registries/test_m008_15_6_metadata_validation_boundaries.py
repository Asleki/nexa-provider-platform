from pathlib import Path
from registries.metadata import RegistryMetadataValidator

ROOT = Path(__file__).resolve().parents[3]


def test_all_prior_metadata_tests_and_boundaries_remain_present():
    required = [
        "tests/unit/registries/metadata/test_registry_metadata_validator.py",
        "tests/unit/registries/test_m008_15_registry_metadata_boundaries.py",
        "tests/unit/registries/test_m008_15_1_registry_capability_boundaries.py",
        "tests/unit/registries/test_m008_15_2_data_classification_boundaries.py",
        "tests/unit/registries/test_m008_15_3_training_eligibility_boundaries.py",
        "tests/unit/registries/test_m008_15_4_provenance_boundaries.py",
        "tests/unit/registries/test_m008_15_5_retention_boundaries.py",
    ]
    assert all((ROOT / path).is_file() for path in required)


def test_validator_is_read_only_and_storage_neutral_by_source_boundary():
    source=(ROOT / "registries/metadata/registry_metadata_validator.py").read_text()
    forbidden=("delete(", "archive(", "persist(", "save(", "requests.", "boto3", "sqlalchemy")
    assert not any(token in source for token in forbidden)
    assert hasattr(RegistryMetadataValidator, "validate_or_raise")


def test_shared_m008_9_validation_files_were_not_replaced_by_metadata_specific_results():
    assert not (ROOT / "registries/metadata/registry_metadata_validation_result.py").exists()
    assert not (ROOT / "registries/metadata/registry_metadata_validation_message.py").exists()
