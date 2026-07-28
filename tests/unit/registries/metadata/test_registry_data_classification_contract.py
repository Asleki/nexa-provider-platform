import pytest

from registries.metadata import (
    RegistryClassificationError,
    RegistryClassificationLevel,
    RegistryDataClassification,
)


def make_classification(**overrides):
    values = {"level": "restricted", "reason": "Registry information"}
    values.update(overrides)
    return RegistryDataClassification(**values)


def test_contract_normalizes_level_reason_and_categories():
    item = make_classification(
        level="  confidential ",
        reason="  Citizen identity and contact information  ",
        data_categories=(" personal.identity ", "PERSONAL.CONTACT"),
    )
    assert item.level is RegistryClassificationLevel.CONFIDENTIAL
    assert item.reason == "Citizen identity and contact information"
    assert item.data_categories == ("PERSONAL.IDENTITY", "PERSONAL.CONTACT")


def test_contract_rejects_invalid_level_as_classification_error():
    with pytest.raises(RegistryClassificationError, match="Unsupported classification"):
        make_classification(level="secret")
    with pytest.raises(RegistryClassificationError, match="cannot be empty"):
        make_classification(level="  ")


def test_contract_preserves_type_error_for_wrong_level_type():
    with pytest.raises(TypeError, match="classification level must be text"):
        make_classification(level=10)


def test_reason_is_required_bounded_and_textual():
    with pytest.raises(TypeError, match="reason must be text"):
        make_classification(reason=None)
    with pytest.raises(RegistryClassificationError, match="reason cannot be empty"):
        make_classification(reason="   ")
    with pytest.raises(RegistryClassificationError, match="cannot exceed 2000"):
        make_classification(reason="x" * 2001)
    assert len(make_classification(reason="x" * 2000).reason) == 2000


def test_boolean_fields_require_actual_booleans():
    boolean_fields = (
        "contains_personal_data",
        "contains_sensitive_personal_data",
        "contains_financial_data",
        "contains_health_data",
        "contains_minor_data",
        "public_disclosure_allowed",
        "masking_required",
    )
    for field_name in boolean_fields:
        with pytest.raises(TypeError, match=field_name):
            make_classification(**{field_name: 1})


def test_sensitive_personal_data_requires_personal_data():
    with pytest.raises(RegistryClassificationError, match="requires contains_personal_data"):
        make_classification(contains_sensitive_personal_data=True)


def test_confidential_levels_cannot_allow_public_disclosure():
    for level in ("confidential", "highly_restricted"):
        with pytest.raises(RegistryClassificationError, match="cannot allow public disclosure"):
            make_classification(level=level, public_disclosure_allowed=True)


def test_public_classification_cannot_require_masking():
    with pytest.raises(RegistryClassificationError, match="cannot require masking"):
        make_classification(level="public", masking_required=True)


def test_public_classification_does_not_force_publication_approval():
    item = make_classification(level="public", public_disclosure_allowed=False)
    assert item.public_disclosure_allowed is False


def test_restricted_classification_can_declare_authorised_public_disclosure():
    item = make_classification(level="restricted", public_disclosure_allowed=True)
    assert item.public_disclosure_allowed is True


def test_domain_flags_do_not_automatically_imply_personal_data():
    item = make_classification(
        contains_financial_data=True,
        contains_health_data=True,
        contains_minor_data=True,
    )
    assert item.contains_personal_data is False


def test_version_requires_positive_non_boolean_integer():
    for value in (True, 1.5, "1"):
        with pytest.raises(TypeError, match="version must be an integer"):
            make_classification(version=value)
    for value in (0, -1):
        with pytest.raises(RegistryClassificationError, match="at least 1"):
            make_classification(version=value)


def test_data_categories_require_hierarchical_semantic_codes():
    item = make_classification(
        data_categories=(
            "CIVIL.BIRTH",
            "EDUCATION.STUDENT.EXAMINATION",
            "MONETARY.ECONOMIC_STATISTIC",
            "ENVIRONMENT.WEATHER",
        )
    )
    assert item.data_categories[-1] == "ENVIRONMENT.WEATHER"

    for value in ("PERSONAL", "personal-contact", ".PERSONAL.IDENTITY"):
        with pytest.raises(RegistryClassificationError, match="hierarchical dotted codes"):
            make_classification(data_categories=(value,))


def test_data_categories_reject_non_iterables_text_and_non_text_members():
    for value in (None, "PERSONAL.IDENTITY", 10):
        with pytest.raises(TypeError, match="data_categories must be an iterable"):
            make_classification(data_categories=value)
    with pytest.raises(TypeError, match="data category codes must be text"):
        make_classification(data_categories=("PERSONAL.IDENTITY", 10))


def test_data_categories_reject_empty_overlong_and_duplicate_codes():
    with pytest.raises(RegistryClassificationError, match="cannot be empty"):
        make_classification(data_categories=("  ",))
    with pytest.raises(RegistryClassificationError, match="cannot exceed 255"):
        make_classification(data_categories=("A." + "B" * 254,))
    with pytest.raises(RegistryClassificationError, match="remain unique"):
        make_classification(data_categories=("personal.identity", " PERSONAL.IDENTITY "))


def test_attribute_keys_are_normalized_and_validated():
    item = make_classification(attributes={" policy ": "P-001"})
    assert dict(item.attributes) == {"policy": "P-001"}

    with pytest.raises(TypeError, match="attribute keys must be text"):
        make_classification(attributes={1: "value"})
    with pytest.raises(RegistryClassificationError, match="cannot be empty"):
        make_classification(attributes={" ": "value"})
    with pytest.raises(RegistryClassificationError, match="remain unique"):
        make_classification(attributes={"policy": 1, " policy ": 2})
