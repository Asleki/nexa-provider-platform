import pytest

from registries.validators import (
    RegistryValidationCollector,
    RegistryValidationMessage,
    ValidationSeverity,
)


def finding(severity):
    return RegistryValidationMessage(
        severity=severity,
        code="COL-001",
        field="registry_id",
        message="Finding.",
    )


def test_collector_builds_valid_and_invalid_results():
    collector = RegistryValidationCollector()
    assert collector.build().valid is True
    collector.add(finding(ValidationSeverity.WARNING))
    assert collector.build().valid is True
    collector.add(finding(ValidationSeverity.ERROR))
    result = collector.build(metadata={"scope": "definition"})
    assert result.invalid is True
    assert result.error_count == 1
    assert result.metadata["scope"] == "definition"


def test_collector_validates_inputs_and_can_clear():
    collector = RegistryValidationCollector()
    with pytest.raises(TypeError):
        collector.add(object())
    with pytest.raises(TypeError):
        collector.extend("not messages")
    collector.extend([finding(ValidationSeverity.INFORMATION)])
    assert not collector.is_empty
    collector.clear()
    assert collector.is_empty
