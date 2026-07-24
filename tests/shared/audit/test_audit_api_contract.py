import pytest
from shared.audit.audit_api_contract import AuditApiContract
from shared.audit.audit_api_operation import AuditApiOperation
from shared.audit.audit_errors import AuditApiContractError

def test_default_contract():
    contract = AuditApiContract()
    assert contract.identifier == "audit.v1"
    assert contract.supports("query")
    assert contract.supports(AuditApiOperation.EXPORT)
    assert contract.supports("unknown") is False

def test_contract_representation_is_immutable():
    result = AuditApiContract().to_dict()
    assert result["operations"] == ("query", "validate_integrity", "export")
    with pytest.raises(TypeError):
        result["version"] = 2

@pytest.mark.parametrize("kwargs", [
    {"name": ""},
    {"version": 0},
    {"version": True},
    {"operations": ()},
    {"operations": (AuditApiOperation.QUERY, AuditApiOperation.QUERY)},
])
def test_invalid_contract_rejected(kwargs):
    with pytest.raises(AuditApiContractError):
        AuditApiContract(**kwargs)
