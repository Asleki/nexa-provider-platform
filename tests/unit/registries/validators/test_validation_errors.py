import pytest

from registries.validators import (
    InvalidRegistryDefinitionError,
    RegistryValidationError,
    RegistryValidationMessage,
    RegistryValidationResult,
    ValidationSeverity,
)


def invalid_result():
    finding = RegistryValidationMessage(
        severity=ValidationSeverity.ERROR,
        code="REG-ERR-001",
        field="registry_code",
        message="Invalid code.",
    )
    return RegistryValidationResult(valid=False, messages=(finding,))


def test_invalid_definition_error_carries_structured_result():
    result = invalid_result()
    error = InvalidRegistryDefinitionError(result)
    assert isinstance(error, RegistryValidationError)
    assert error.result is result
    assert "1 error(s)" in str(error)


def test_invalid_definition_error_rejects_wrong_or_valid_result():
    with pytest.raises(TypeError):
        InvalidRegistryDefinitionError(object())
    with pytest.raises(ValueError):
        InvalidRegistryDefinitionError(RegistryValidationResult(valid=True))
