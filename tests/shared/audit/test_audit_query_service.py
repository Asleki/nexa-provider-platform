from datetime import datetime, timedelta, timezone
from shared.audit import (
    AuditAction, AuditOutcome, AuditQuery, AuditQueryService,
    AuditRecord, MemoryAuditRepository,
)

def make_record(audit_id, *, actor_id="OP-1", action=AuditAction.READ, minute=0):
    return AuditRecord(
        audit_id=audit_id,
        version=1,
        recorded_at=datetime(2026, 7, 20, 8, minute, tzinfo=timezone.utc),
        action=action,
        outcome=AuditOutcome.SUCCESS,
        actor_id=actor_id,
        actor_type="operator",
        target_namespace="provider",
        target_type="citizen",
        target_id=f"C-{audit_id}",
        runtime_id="runtime-1",
        runtime_mode="simulation",
        source="cli",
    )

def test_service_filters_with_and_semantics_and_orders_results():
    repo = MemoryAuditRepository()
    repo.append(make_record("AUD-2", actor_id="OP-1", minute=2))
    repo.append(make_record("AUD-1", actor_id="OP-1", minute=1))
    repo.append(make_record("AUD-3", actor_id="OP-2", minute=3))

    result = AuditQueryService(repo).query(
        AuditQuery(actor_id="OP-1", action=AuditAction.READ)
    )

    assert [record.audit_id for record in result.records] == ["AUD-1", "AUD-2"]
    assert result.count == 2

def test_service_supports_inclusive_time_range():
    repo = MemoryAuditRepository()
    repo.append(make_record("AUD-1", minute=1))
    repo.append(make_record("AUD-2", minute=2))
    result = AuditQueryService(repo).query(
        AuditQuery(
            recorded_from=datetime(2026, 7, 20, 8, 2, tzinfo=timezone.utc),
            recorded_to=datetime(2026, 7, 20, 8, 2, tzinfo=timezone.utc),
        )
    )
    assert [record.audit_id for record in result.records] == ["AUD-2"]

def test_query_does_not_mutate_repository():
    repo = MemoryAuditRepository()
    repo.append(make_record("AUD-1"))
    service = AuditQueryService(repo)
    service.query(AuditQuery())
    assert repo.count().count == 1
