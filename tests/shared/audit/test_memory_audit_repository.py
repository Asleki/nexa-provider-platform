from datetime import datetime, timezone
import pytest

from shared.audit import AuditAction, AuditOutcome, AuditRecord
from shared.audit.audit_errors import AuditDuplicateRecordError, AuditRecordNotFoundError
from shared.audit.audit_repository_types import AuditRepositoryOperation, AuditRepositoryType
from shared.audit.memory_audit_repository import MemoryAuditRepository


def make_record(audit_id: str) -> AuditRecord:
    return AuditRecord(audit_id=audit_id, version=1, recorded_at=datetime.now(timezone.utc), action=AuditAction.CREATE, outcome=AuditOutcome.SUCCESS, actor_id="A", actor_type="user", target_namespace="n", target_type="t", target_id=audit_id, runtime_id="r", runtime_mode="test", source="unit")


def test_repository_starts_empty() -> None:
    repo = MemoryAuditRepository()
    assert repo.repository_type is AuditRepositoryType.MEMORY
    assert repo.count().count == 0
    assert repo.list_all().records == ()


def test_append_get_exists_count_and_order() -> None:
    repo = MemoryAuditRepository(" audit_repo ")
    first, second = make_record("AUD-1"), make_record("AUD-2")
    appended = repo.append(first)
    repo.append(second)
    assert appended.operation is AuditRepositoryOperation.APPEND
    assert appended.record is first
    assert repo.get("AUD-1").record is first
    assert repo.exists("AUD-1").exists is True
    assert repo.exists("AUD-X").exists is False
    assert repo.count().count == 2
    assert repo.list_all().records == (first, second)


def test_duplicate_and_missing_records_raise_specific_errors() -> None:
    repo = MemoryAuditRepository()
    record = make_record("AUD-1")
    repo.append(record)
    with pytest.raises(AuditDuplicateRecordError):
        repo.append(record)
    with pytest.raises(AuditRecordNotFoundError):
        repo.get("AUD-X")


def test_repository_exposes_no_destructive_operations() -> None:
    repo = MemoryAuditRepository()
    assert not hasattr(repo, "delete")
    assert not hasattr(repo, "clear")
    assert not hasattr(repo, "update")
