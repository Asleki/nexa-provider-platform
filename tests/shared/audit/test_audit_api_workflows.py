"""M007.9 workflow tests for the framework-neutral Audit API contracts."""
from datetime import UTC, datetime, timedelta
import pytest
from shared.audit.audit_api_contract import AuditApiContract
from shared.audit.audit_api_operation import AuditApiOperation
from shared.audit.audit_api_request import AuditApiRequest
from shared.audit.audit_api_response import AuditApiResponse

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)

@pytest.mark.parametrize("operation", tuple(AuditApiOperation))
def test_supported_operation_round_trip_preserves_request_correlation(operation):
    contract = AuditApiContract()
    request = AuditApiRequest(request_id=f"REQ-{operation.value}", operation=operation, requested_at=NOW, payload={"limit": 10})
    response = AuditApiResponse.succeeded(request_id=request.request_id, operation=request.operation, completed_at=NOW + timedelta(seconds=1), data={"accepted": True})
    assert contract.supports(request.operation)
    assert response.request_id == request.request_id
    assert response.operation is request.operation
    assert response.completed_at >= request.requested_at
    assert response.to_dict()["success"] is True

@pytest.mark.parametrize("operation", tuple(AuditApiOperation))
def test_failed_operation_round_trip_has_error_only(operation):
    request = AuditApiRequest(request_id="REQ-FAIL", operation=operation, requested_at=NOW)
    response = AuditApiResponse.failed(request_id=request.request_id, operation=request.operation, completed_at=NOW, error={"code": "AUDIT_TEST_FAILURE"})
    data = response.to_dict()
    assert data["success"] is False
    assert data["data"] is None
    assert data["error"] == {"code": "AUDIT_TEST_FAILURE"}

def test_contract_declares_every_enum_operation_exactly_once():
    contract = AuditApiContract()
    assert contract.operations == tuple(AuditApiOperation)
    assert len(contract.operations) == len(set(contract.operations))
