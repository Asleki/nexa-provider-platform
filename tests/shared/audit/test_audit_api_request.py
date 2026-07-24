from datetime import datetime, timezone
from dataclasses import FrozenInstanceError
import pytest
from shared.audit.audit_api_request import AuditApiRequest
from shared.audit.audit_api_operation import AuditApiOperation
from shared.audit.audit_errors import AuditApiValidationError

def make_request(**changes):
    values = dict(
        request_id=" req-1 ",
        operation="query",
        requested_at=datetime(2026, 7, 24, tzinfo=timezone.utc),
        payload={"limit": 10},
        metadata={"source": "test"},
    )
    values.update(changes)
    return AuditApiRequest(**values)

def test_request_normalizes_and_freezes():
    request = make_request()
    assert request.request_id == "req-1"
    assert request.operation is AuditApiOperation.QUERY
    assert dict(request.payload) == {"limit": 10}
    with pytest.raises(TypeError):
        request.payload["limit"] = 20

def test_to_dict_is_detached():
    request = make_request()
    result = request.to_dict()
    result["payload"]["limit"] = 20
    assert request.payload["limit"] == 10

@pytest.mark.parametrize("changes", [
    {"request_id": ""},
    {"requested_at": datetime(2026, 7, 24)},
    {"payload": []},
    {"metadata": []},
])
def test_invalid_request_rejected(changes):
    with pytest.raises(AuditApiValidationError):
        make_request(**changes)
