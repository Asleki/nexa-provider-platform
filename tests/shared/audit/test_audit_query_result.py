import pytest
from shared.audit import AuditQuery, AuditQueryResult, AuditQueryResultError

def test_empty_result_is_immutable_and_reports_count():
    result = AuditQueryResult(query=AuditQuery(), metadata={"source": "test"})
    assert result.count == 0
    assert not result.found
    assert result.metadata["source"] == "test"
    with pytest.raises(TypeError):
        result.metadata["source"] = "changed"

def test_result_requires_query():
    with pytest.raises(AuditQueryResultError):
        AuditQueryResult(query=None)
