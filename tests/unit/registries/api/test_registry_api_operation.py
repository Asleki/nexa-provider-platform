import pytest
from registries.api import RegistryApiOperation, RegistryApiValidationError

def test_operations_are_stable_and_clear_is_excluded():
    assert RegistryApiOperation.REGISTER.value == "register"
    assert "clear" not in {item.value for item in RegistryApiOperation}

def test_operation_parse_normalizes_and_rejects_unknown():
    assert RegistryApiOperation.parse(" GET ") is RegistryApiOperation.GET
    with pytest.raises(RegistryApiValidationError): RegistryApiOperation.parse("clear")
