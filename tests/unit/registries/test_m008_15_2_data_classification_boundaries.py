from dataclasses import fields
from pathlib import Path

from registries.metadata import RegistryDataClassification


ROOT = Path(__file__).resolve().parents[3]
METADATA_TESTS = ROOT / "tests" / "unit" / "registries" / "metadata"


def test_m008_15_2_appends_tests_without_replacing_existing_tests():
    assert (METADATA_TESTS / "test_registry_data_classification.py").is_file()
    assert (METADATA_TESTS / "test_registry_capability.py").is_file()
    assert (METADATA_TESTS / "test_registry_capability_contract.py").is_file()
    assert (METADATA_TESTS / "test_registry_classification_level_contract.py").is_file()
    assert (METADATA_TESTS / "test_registry_data_classification_contract.py").is_file()
    assert (METADATA_TESTS / "test_registry_data_classification_serialization.py").is_file()
    assert (METADATA_TESTS / "test_registry_data_classification_immutability.py").is_file()


def test_classification_contract_excludes_sibling_milestone_responsibilities():
    field_names = {field.name for field in fields(RegistryDataClassification)}
    forbidden = {
        "training_allowed",
        "training_status",
        "training_eligibility",
        "provenance",
        "source_type",
        "retention",
        "retention_mode",
        "permission",
        "permissions",
        "encryption_key",
        "consent",
        "relationship",
        "simulation_supported",
        "production_supported",
        "export_allowed",
        "cross_border_allowed",
    }
    assert field_names.isdisjoint(forbidden)


def test_classification_contract_keeps_declaration_only_fields():
    field_names = {field.name for field in fields(RegistryDataClassification)}
    assert {
        "level",
        "reason",
        "contains_personal_data",
        "contains_sensitive_personal_data",
        "contains_financial_data",
        "contains_health_data",
        "contains_minor_data",
        "public_disclosure_allowed",
        "masking_required",
        "version",
        "data_categories",
        "attributes",
    } <= field_names


def test_future_domains_share_semantic_category_contract_without_new_engines():
    item = RegistryDataClassification(
        level="restricted",
        reason="Cross-domain registry metadata",
        data_categories=(
            "CIVIL.BIRTH",
            "EDUCATION.SCHOOL",
            "HEALTH.HOSPITAL",
            "FINANCIAL.BANK",
            "TELECOM.SUBSCRIBER",
            "ENVIRONMENT.WEATHER",
            "BUSINESS.MANUFACTURER",
        ),
    )
    assert len(item.data_categories) == 7
