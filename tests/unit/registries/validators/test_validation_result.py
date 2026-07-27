from types import MappingProxyType

import pytest

from registries.validators import (
    RegistryValidationMessage,
    RegistryValidationResult,
    ValidationSeverity,
)


def message(severity=ValidationSeverity.ERROR, field="registry_code"):
    return RegistryValidationMessage(
        severity=severity,
        code="REG-TEST-001",
        field=field,
        message="Finding.",
        suggestion="Fix it.",
    )


def test_result_is_immutable_and_derives_filtered_views():
    result = RegistryValidationResult(valid=False, messages=(message(),), metadata={"run": 1})
    assert result.invalid is True
    assert result.error_count == 1
    assert result.errors == result.messages
    assert result.messages_for("registry_code") == result.messages
    assert isinstance(result.metadata, MappingProxyType)
    with pytest.raises(TypeError):
        result.metadata["run"] = 2


def test_result_rejects_inconsistent_valid_flag():
    with pytest.raises(ValueError):
        RegistryValidationResult(valid=True, messages=(message(),))
    with pytest.raises(ValueError):
        RegistryValidationResult(valid=False, messages=())


def test_result_round_trip_is_deterministic():
    original = RegistryValidationResult(
        valid=True,
        messages=(message(ValidationSeverity.WARNING),),
        metadata={"validator": "registry"},
    )
    restored = RegistryValidationResult.from_dict(original.to_dict())
    assert restored == original
    assert "1 warning(s)" in restored.summary


def test_result_rejects_malformed_payloads():
    with pytest.raises(TypeError):
        RegistryValidationResult.from_dict([])
    with pytest.raises(TypeError):
        RegistryValidationResult.from_dict({"valid": "yes", "messages": []})
    with pytest.raises(TypeError):
        RegistryValidationResult(valid=True, messages=(object(),))
