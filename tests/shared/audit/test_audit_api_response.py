from datetime import datetime, timezone
import pytest
from shared.audit.audit_api_response import AuditApiResponse
from shared.audit.audit_api_operation import AuditApiOperation
from shared.audit.audit_errors import AuditApiResultError

NOW = datetime(2026, 7, 24, tzinfo=timezone.utc)

def test_success_factory():
    response = AuditApiResponse.succeeded(
        request_id="req-1", operation="query", completed_at=NOW,
        data={"count": 1}
    )
    assert response.success is True
    assert response.error is None
    assert response.to_dict()["data"] == {"count": 1}

def test_failure_factory():
    response = AuditApiResponse.failed(
        request_id="req-1", operation=AuditApiOperation.EXPORT,
        completed_at=NOW, error={"code": "failed"}
    )
    assert response.success is False
    assert response.data is None

@pytest.mark.parametrize("kwargs", [
    dict(request_id="req", operation="query", completed_at=NOW,
         success=True, error={"code": "bad"}),
    dict(request_id="req", operation="query", completed_at=NOW,
         success=False, data={"x": 1}, error={"code": "bad"}),
    dict(request_id="req", operation="query", completed_at=NOW,
         success=False),
    dict(request_id="", operation="query", completed_at=NOW, success=True),
])
def test_invalid_response_rejected(kwargs):
    with pytest.raises(AuditApiResultError):
        AuditApiResponse(**kwargs)
