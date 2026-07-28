import pytest

from registries.metadata import RegistryClassificationLevel


def test_classification_levels_keep_stable_order_and_values():
    assert list(RegistryClassificationLevel) == [
        RegistryClassificationLevel.PUBLIC,
        RegistryClassificationLevel.INTERNAL,
        RegistryClassificationLevel.RESTRICTED,
        RegistryClassificationLevel.CONFIDENTIAL,
        RegistryClassificationLevel.HIGHLY_RESTRICTED,
    ]
    assert [level.value for level in RegistryClassificationLevel] == [10, 20, 30, 40, 50]


def test_classification_levels_keep_stable_codes():
    assert [level.code for level in RegistryClassificationLevel] == [
        "public",
        "internal",
        "restricted",
        "confidential",
        "highly_restricted",
    ]
    assert str(RegistryClassificationLevel.HIGHLY_RESTRICTED) == "highly_restricted"


def test_from_value_accepts_members_and_normalized_text():
    assert (
        RegistryClassificationLevel.from_value(RegistryClassificationLevel.INTERNAL)
        is RegistryClassificationLevel.INTERNAL
    )
    assert (
        RegistryClassificationLevel.from_value("  highly_restricted  ")
        is RegistryClassificationLevel.HIGHLY_RESTRICTED
    )
    assert (
        RegistryClassificationLevel.from_value("Confidential")
        is RegistryClassificationLevel.CONFIDENTIAL
    )


def test_from_value_rejects_empty_and_unsupported_text():
    with pytest.raises(ValueError, match="cannot be empty"):
        RegistryClassificationLevel.from_value("   ")
    with pytest.raises(ValueError, match="Unsupported classification level"):
        RegistryClassificationLevel.from_value("secret")


def test_from_value_rejects_non_text_values():
    for value in (None, 10, True, object()):
        with pytest.raises(TypeError, match="classification level must be text"):
            RegistryClassificationLevel.from_value(value)
