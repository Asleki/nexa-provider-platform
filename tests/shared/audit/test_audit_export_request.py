from datetime import datetime, timedelta, timezone
import pytest

from shared.audit.audit_errors import AuditExportValidationError
from shared.audit.audit_export_request import AuditExportRequest
from shared.audit.audit_query import AuditQuery
from shared.audit.audit_query_result import AuditQueryResult


def test_request_normalizes_and_freezes_values() -> None:
    local = timezone(timedelta(hours=2))
    request = AuditExportRequest(
        export_id=" EXP-1 ",
        generated_at=datetime(2026, 7, 23, 10, tzinfo=local),
        query_result=AuditQueryResult(query=AuditQuery()),
        metadata={"purpose": "review"},
    )
    assert request.export_id == "EXP-1"
    assert request.generated_at.tzinfo == timezone.utc
    assert request.metadata["purpose"] == "review"
    with pytest.raises(TypeError):
        request.metadata["purpose"] = "changed"


@pytest.mark.parametrize("value", ["", "   ", None, 7])
def test_request_rejects_invalid_export_id(value) -> None:
    with pytest.raises(AuditExportValidationError):
        AuditExportRequest(
            export_id=value,
            generated_at=datetime.now(timezone.utc),
            query_result=AuditQueryResult(query=AuditQuery()),
        )


def test_request_rejects_naive_datetime() -> None:
    with pytest.raises(AuditExportValidationError):
        AuditExportRequest(
            export_id="EXP-1",
            generated_at=datetime(2026, 1, 1),
            query_result=AuditQueryResult(query=AuditQuery()),
        )
