"""M007.10 stabilization tests for framework-neutral Audit API contracts."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from shared.audit.audit_api_contract import AuditApiContract
from shared.audit.audit_api_operation import AuditApiOperation
from shared.audit.audit_api_request import AuditApiRequest
from shared.audit.audit_api_response import AuditApiResponse


NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("operation", tuple(AuditApiOperation))
def test_request_response_round_trip_preserves_contract_identity(
    operation: AuditApiOperation,
) -> None:
    contract = AuditApiContract()

    request = AuditApiRequest(
        request_id=f"REQ-{operation.value}",
        operation=operation,
        requested_at=NOW,
        payload={"operation": operation.value},
        metadata={"contract": contract.identifier},
    )
    response = AuditApiResponse.succeeded(
        request_id=request.request_id,
        operation=request.operation,
        completed_at=NOW,
        data={"accepted": True},
        metadata={"contract": contract.identifier},
    )

    assert contract.supports(operation)
    assert response.request_id == request.request_id
    assert response.operation is request.operation
    assert response.metadata["contract"] == contract.identifier


def test_success_and_failure_envelopes_remain_mutually_exclusive() -> None:
    success = AuditApiResponse.succeeded(
        request_id="REQ-SUCCESS",
        operation=AuditApiOperation.QUERY,
        completed_at=NOW,
        data={"count": 0},
    )
    failure = AuditApiResponse.failed(
        request_id="REQ-FAILURE",
        operation=AuditApiOperation.QUERY,
        completed_at=NOW,
        error={"code": "AUDIT_QUERY_FAILED"},
    )

    assert success.success is True
    assert success.error is None
    assert failure.success is False
    assert failure.data is None


def test_request_and_response_serialization_are_detached() -> None:
    request = AuditApiRequest(
        request_id="REQ-DETACHED",
        operation=AuditApiOperation.EXPORT,
        requested_at=NOW,
        payload={"format": "json"},
        metadata={"source": "test"},
    )
    response = AuditApiResponse.succeeded(
        request_id=request.request_id,
        operation=request.operation,
        completed_at=NOW,
        data={"records": 1},
        metadata={"source": "test"},
    )

    request_dict = request.to_dict()
    response_dict = response.to_dict()

    request_dict["payload"]["format"] = "csv"
    response_dict["data"]["records"] = 99

    assert request.payload["format"] == "json"
    assert response.data["records"] == 1


def test_contract_serialization_preserves_stable_operation_order() -> None:
    contract = AuditApiContract()
    serialized = contract.to_dict()

    assert serialized["identifier"] == "audit.v1"
    assert serialized["operations"] == (
        "query",
        "validate_integrity",
        "export",
    )
