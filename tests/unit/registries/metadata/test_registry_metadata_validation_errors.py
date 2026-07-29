import pytest
from registries.metadata import InvalidRegistryMetadataError
from registries.validators import RegistryValidationMessage, RegistryValidationResult, ValidationSeverity


def invalid_result():
    return RegistryValidationResult(False, (RegistryValidationMessage(ValidationSeverity.ERROR, "X", "field", "bad"),))


def test_invalid_metadata_error_carries_result():
    result = invalid_result(); error = InvalidRegistryMetadataError(result)
    assert error.result is result and str(error) == result.summary


def test_invalid_metadata_error_rejects_valid_or_wrong_result():
    with pytest.raises(ValueError): InvalidRegistryMetadataError(RegistryValidationResult(True))
    with pytest.raises(TypeError): InvalidRegistryMetadataError(object())
