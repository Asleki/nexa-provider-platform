import pytest
from registries.ports import RegistryAuditPort

def test_registry_audit_port_is_abstract():
    with pytest.raises(TypeError): RegistryAuditPort()
