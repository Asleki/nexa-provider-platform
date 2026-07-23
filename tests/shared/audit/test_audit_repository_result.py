from datetime import datetime, timezone
from types import MappingProxyType
import pytest

from shared.audit import AuditAction, AuditOutcome, AuditRecord
from shared.audit.audit_repository_result import AuditRepositoryResult
from shared.audit.audit_repository_types import AuditRepositoryOperation


def make_record(audit_id: str = "AUD-001") -> AuditRecord:
    return AuditRecord(audit_id=audit_id, version=1, recorded_at=datetime.now(timezone.utc), action=AuditAction.CREATE, outcome=AuditOutcome.SUCCESS, actor_id="ACT-1", actor_type="user", target_namespace="provider", target_type="profile", target_id="P-1", runtime_id="RUN-1", runtime_mode="test", source="unit")


def test_appended_result_is_immutable_and_linked() -> None:
    record = make_record()
    result = AuditRepositoryResult.appended(repository=" repo ", record=record, metadata={"x": 1})
    assert result.success is True
    assert result.operation is AuditRepositoryOperation.APPEND
    assert result.repository == "repo"
    assert result.audit_id == record.audit_id
    assert result.record is record
    assert result.records_affected == 1
    assert isinstance(result.metadata, MappingProxyType)


def test_listed_result_preserves_order_and_count() -> None:
    first, second = make_record("AUD-1"), make_record("AUD-2")
    result = AuditRepositoryResult.listed(repository="repo", records=(first, second))
    assert result.records == (first, second)
    assert result.count == 2
    assert result.records_affected == 2


def test_existence_and_count_results() -> None:
    exists = AuditRepositoryResult.existence_checked(repository="repo", audit_id="AUD-1", exists=True)
    counted = AuditRepositoryResult.counted(repository="repo", count=3)
    assert exists.exists is True
    assert counted.count == 3


def test_rejects_invalid_record_and_mismatched_identifier() -> None:
    with pytest.raises(TypeError, match="record must be an AuditRecord"):
        AuditRepositoryResult(True, AuditRepositoryOperation.READ, "repo", record=object())
    with pytest.raises(ValueError, match="must match"):
        AuditRepositoryResult(True, AuditRepositoryOperation.READ, "repo", audit_id="OTHER", record=make_record())
