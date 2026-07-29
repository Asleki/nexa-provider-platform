from pathlib import Path

from registries.metadata import RegistryTrainingEligibility

ROOT = Path(__file__).resolve().parents[3]


def test_prior_metadata_tests_and_boundaries_remain_present():
    metadata_tests = ROOT / "tests" / "unit" / "registries" / "metadata"
    for name in (
        "test_registry_training_eligibility.py",
        "test_registry_capability.py",
        "test_registry_data_classification.py",
    ):
        assert (metadata_tests / name).is_file()
    registry_tests = ROOT / "tests" / "unit" / "registries"
    for name in (
        "test_m008_15_registry_metadata_boundaries.py",
        "test_m008_15_1_registry_capability_boundaries.py",
        "test_m008_15_2_data_classification_boundaries.py",
    ):
        assert (registry_tests / name).is_file()


def test_training_eligibility_remains_declaration_only():
    fields = RegistryTrainingEligibility.__dataclass_fields__
    forbidden = {
        "classification_level",
        "contains_personal_data",
        "source_id",
        "source_type",
        "retention_mode",
        "retention_days",
        "dataset_id",
        "model_id",
        "training_job_id",
        "consent_id",
        "approval_id",
    }
    assert forbidden.isdisjoint(fields)


def test_training_eligibility_has_no_training_or_policy_execution_imports():
    source = (
        ROOT
        / "registries"
        / "metadata"
        / "registry_training_eligibility.py"
    ).read_text()
    forbidden = (
        "tensorflow",
        "torch",
        "sklearn",
        "transformers",
        "fit(",
        "train(",
        "encrypt(",
        "anonymise(",
        "anonymize(",
        "approve(",
        "ConsentRepository",
        "ModelRepository",
        "DatasetRepository",
    )
    for token in forbidden:
        assert token not in source


def test_open_purpose_codes_support_future_domains_without_new_fields():
    scenarios = (
        "education.school_planning",
        "health.capacity_forecasting",
        "financial.failure_analysis",
        "simulation.calibration",
        "telecom.coverage_planning",
    )
    item = RegistryTrainingEligibility(
        "conditionally_eligible",
        "Controlled domain-specific uses",
        purpose_restrictions=scenarios,
    )
    assert item.purpose_restrictions == scenarios
