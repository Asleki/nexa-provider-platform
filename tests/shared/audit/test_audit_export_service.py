from datetime import datetime, timezone
import pytest

from shared.audit.audit_action import AuditAction
from shared.audit.audit_errors import AuditExportValidationError
from shared.audit.audit_export_request import AuditExportRequest
from shared.audit.audit_export_service import AuditExportService
from shared.audit.audit_outcome import AuditOutcome
from shared.audit.audit_query import AuditQuery
from shared.audit.audit_query_result import AuditQueryResult
from shared.audit.audit_record import AuditRecord


def make_record() -> AuditRecord:
    return AuditRecord(
        audit_id="A-1",
        version=1,
        recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        action=next(iter(AuditAction)),
        outcome=next(iter(AuditOutcome)),
        actor_id="actor-1",
        actor_type="operator",
        target_namespace="provider",
        target_type="citizen",
        target_id="target-1",
        runtime_id="runtime-1",
        runtime_mode="simulation",
        source="test",
        metadata={"approved": True},
    )


def test_service_exports_query_result_without_mutating_source() -> None:
    record = make_record()
    query = AuditQuery(actor_id="actor-1")
    query_result = AuditQueryResult(
        query=query,
        records=(record,),
        metadata={"page": 1},
    )
    request = AuditExportRequest(
        export_id="EXP-1",
        generated_at=datetime(2026, 7, 23, tzinfo=timezone.utc),
        query_result=query_result,
        metadata={"reason": "compliance"},
    )

    result = AuditExportService().export(request)

    assert result.export_id == "EXP-1"
    assert result.schema_version == 1
    assert result.count == 1
    assert result.records[0]["audit_id"] == "A-1"
    assert result.query["actor_id"] == "actor-1"
    assert result.query_metadata["page"] == 1
    assert result.metadata["reason"] == "compliance"
    assert query_result.records[0] is record


def test_service_is_deterministic_for_same_request() -> None:
    request = AuditExportRequest(
        export_id="EXP-1",
        generated_at=datetime(2026, 7, 23, tzinfo=timezone.utc),
        query_result=AuditQueryResult(
            query=AuditQuery(),
            records=(make_record(),),
        ),
    )
    service = AuditExportService()
    assert service.export(request).to_dict() == service.export(request).to_dict()


def test_service_rejects_invalid_request() -> None:
    with pytest.raises(AuditExportValidationError):
        AuditExportService().export(object())
