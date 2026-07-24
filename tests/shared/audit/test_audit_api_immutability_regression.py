"""M007.9 regression tests for defensive copying and immutable envelopes."""
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from types import MappingProxyType
import pytest
from shared.audit.audit_api_contract import AuditApiContract
from shared.audit.audit_api_operation import AuditApiOperation
from shared.audit.audit_api_request import AuditApiRequest
from shared.audit.audit_api_response import AuditApiResponse

NOW = datetime(2026, 7, 24, tzinfo=UTC)

def test_request_defensively_copies_payload_and_metadata():
    payload={"query":"original"}; metadata={"channel":"test"}
    request=AuditApiRequest("REQ-1", AuditApiOperation.QUERY, NOW, payload, metadata)
    payload["query"]="changed"; metadata["channel"]="changed"
    assert request.payload == {"query":"original"}
    assert request.metadata == {"channel":"test"}
    assert isinstance(request.payload, MappingProxyType)
    with pytest.raises(TypeError): request.payload["query"]="mutated"

def test_response_defensively_copies_data_error_and_metadata():
    data={"count":1}; metadata={"trace":"T-1"}
    response=AuditApiResponse.succeeded(request_id="REQ-1",operation=AuditApiOperation.QUERY,completed_at=NOW,data=data,metadata=metadata)
    data["count"]=99; metadata["trace"]="changed"
    assert response.data == {"count":1}
    assert response.metadata == {"trace":"T-1"}

def test_to_dict_returns_independent_mutable_copies():
    request=AuditApiRequest("REQ-1",AuditApiOperation.EXPORT,NOW,{"format":"json"},{"actor":"A"})
    exported=request.to_dict()
    exported["payload"]["format"]="csv"; exported["metadata"]["actor"]="B"
    assert request.payload["format"]=="json"
    assert request.metadata["actor"]=="A"

def test_contract_and_envelopes_are_frozen():
    contract=AuditApiContract()
    request=AuditApiRequest("REQ-1",AuditApiOperation.QUERY,NOW)
    response=AuditApiResponse.succeeded(request_id="REQ-1",operation=AuditApiOperation.QUERY,completed_at=NOW)
    for obj, attr, value in ((contract,"version",2),(request,"request_id","X"),(response,"success",False)):
        with pytest.raises(FrozenInstanceError):
            setattr(obj,attr,value)
