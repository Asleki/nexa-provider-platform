from registries import validators
from registries.validators import (
    REGISTRY_VALIDATION_CHECKLIST,
    registry_validation_checklist,
)


def test_validator_public_api_exports_m008_9_symbols():
    expected = {
        "InvalidRegistryDefinitionError",
        "RegistryValidationCollector",
        "RegistryValidationError",
        "RegistryValidationMessage",
        "RegistryValidationResult",
        "RegistryValidator",
        "ValidationSeverity",
    }
    assert expected <= set(validators.__all__)
    for name in expected:
        assert hasattr(validators, name)


def test_registry_validation_checklist_is_stable_and_immutable():
    assert registry_validation_checklist() is REGISTRY_VALIDATION_CHECKLIST
    assert REGISTRY_VALIDATION_CHECKLIST == (
        "registry_id",
        "registry_code",
        "registry_name",
        "family",
        "status",
        "description",
        "version",
        "metadata",
    )
