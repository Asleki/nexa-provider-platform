"""M007.9 boundary and failure-isolation tests."""
from datetime import UTC, datetime
import pytest
from shared.audit.audit_api_contract import AuditApiContract
from shared.audit.audit_api_operation import AuditApiOperation
from shared.audit.audit_api_request import AuditApiRequest
from shared.audit.audit_api_response import AuditApiResponse
from shared.audit.audit_errors import AuditApiContractError, AuditApiResultError, AuditApiValidationError

NOW=datetime(2026,7,24,tzinfo=UTC)

@pytest.mark.parametrize("value",[None,1,object(),"","   ","unknown"])
def test_operation_parse_rejects_invalid_values(value):
    with pytest.raises(AuditApiValidationError):
        AuditApiOperation.parse(value)

@pytest.mark.parametrize("value",[None,1,[],()])
def test_request_rejects_non_mapping_payload(value):
    with pytest.raises(AuditApiValidationError):
        AuditApiRequest("REQ-1",AuditApiOperation.QUERY,NOW,payload=value)

@pytest.mark.parametrize("kwargs",[
    {"success":True,"error":{"code":"X"}},
    {"success":False,"data":{"count":1},"error":{"code":"X"}},
    {"success":False},
])
def test_response_enforces_success_failure_exclusivity(kwargs):
    with pytest.raises(AuditApiResultError):
        AuditApiResponse(request_id="REQ-1",operation=AuditApiOperation.QUERY,completed_at=NOW,**kwargs)

@pytest.mark.parametrize("operations",[(),(AuditApiOperation.QUERY,AuditApiOperation.QUERY)])
def test_contract_rejects_empty_or_duplicate_operations(operations):
    with pytest.raises(AuditApiContractError):
        AuditApiContract(operations=operations)

def test_supports_is_safe_for_untrusted_input():
    contract=AuditApiContract()
    for value in (None,object(),"","invalid"):
        assert contract.supports(value) is False
