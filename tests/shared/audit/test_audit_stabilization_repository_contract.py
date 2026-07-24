"""M007.10 stabilization tests for MemoryAuditRepository behavior."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest

from shared.audit.audit_action import AuditAction
from shared.audit.audit_errors import AuditDuplicateRecordError
from shared.audit.audit_outcome import AuditOutcome
from shared.audit.audit_record import AuditRecord
from shared.audit.memory_audit_repository import MemoryAuditRepository


def _record(index: int) -> AuditRecord:
    return AuditRecord(
        audit_id=f"AUD-STABLE-{index:03d}",
        version=1,
        recorded_at=datetime(2026, 7, 24, 12, index % 60, tzinfo=timezone.utc),
        action=AuditAction.CREATE,
        outcome=AuditOutcome.SUCCESS,
        actor_id="ACTOR-001",
        actor_type="employee",
        target_namespace="npp",
        target_type="provider",
        target_id=f"PROVIDER-{index:03d}",
        runtime_id="RUNTIME-001",
        runtime_mode="simulation",
        source="stabilization-test",
        metadata={"sequence": index},
    )


def test_repository_operation_results_remain_correlated() -> None:
    repository = MemoryAuditRepository("stabilization")

    appended = repository.append(_record(1))
    found = repository.get("AUD-STABLE-001")
    exists = repository.exists("AUD-STABLE-001")
    counted = repository.count()
    listed = repository.list_all()

    assert appended.record.audit_id == "AUD-STABLE-001"
    assert found.record is appended.record
    assert exists.exists is True
    assert counted.count == 1
    assert listed.count == 1
    assert listed.records == (appended.record,)


def test_repository_remains_append_only_for_duplicate_identifiers() -> None:
    repository = MemoryAuditRepository()
    original = _record(1)

    repository.append(original)

    with pytest.raises(AuditDuplicateRecordError):
        repository.append(_record(1))

    assert repository.count().count == 1
    assert repository.get(original.audit_id).record is original


def test_repository_concurrent_appends_do_not_lose_records() -> None:
    repository = MemoryAuditRepository("concurrent-stabilization")
    records = tuple(_record(index) for index in range(40))

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = tuple(executor.map(repository.append, records))

    assert len(results) == 40
    assert repository.count().count == 40

    listed = repository.list_all()
    assert len(listed.records) == 40
    assert {record.audit_id for record in listed.records} == {
        record.audit_id for record in records
    }


def test_list_snapshots_do_not_change_after_later_appends() -> None:
    repository = MemoryAuditRepository()

    repository.append(_record(1))
    first_snapshot = repository.list_all()

    repository.append(_record(2))
    second_snapshot = repository.list_all()

    assert tuple(record.audit_id for record in first_snapshot.records) == (
        "AUD-STABLE-001",
    )
    assert tuple(record.audit_id for record in second_snapshot.records) == (
        "AUD-STABLE-001",
        "AUD-STABLE-002",
    )
