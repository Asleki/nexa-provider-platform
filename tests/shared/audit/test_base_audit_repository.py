from datetime import datetime, timezone
import pytest

from shared.audit import AuditAction, AuditOutcome, AuditRecord
from shared.audit.audit_errors import AuditInvalidRecordError, AuditRepositoryConfigurationError
from shared.audit.audit_repository_result import AuditRepositoryResult
from shared.audit.audit_repository_types import AuditRepositoryOperation, AuditRepositoryType
from shared.audit.base_audit_repository import BaseAuditRepository


class StubRepository(BaseAuditRepository):
    def append(self, record): raise NotImplementedError
    def get(self, audit_id): raise NotImplementedError
    def list_all(self): raise NotImplementedError
    def exists(self, audit_id): raise NotImplementedError
    def count(self): raise NotImplementedError


def make_record() -> AuditRecord:
    return AuditRecord(audit_id="AUD-1", version=1, recorded_at=datetime.now(timezone.utc), action=AuditAction.CREATE, outcome=AuditOutcome.SUCCESS, actor_id="A", actor_type="user", target_namespace="n", target_type="t", target_id="1", runtime_id="r", runtime_mode="test", source="unit")


def test_identity_is_normalized() -> None:
    repo = StubRepository(repository_name=" test_repo ", repository_type=AuditRepositoryType.MEMORY)
    assert repo.repository_name == "test_repo"
    assert repo.repository_type is AuditRepositoryType.MEMORY


def test_invalid_configuration_is_rejected() -> None:
    with pytest.raises(AuditRepositoryConfigurationError):
        StubRepository(repository_name=" ", repository_type=AuditRepositoryType.MEMORY)
    with pytest.raises(AuditRepositoryConfigurationError):
        StubRepository(repository_name="x", repository_type="memory")


def test_identifier_and_record_validation() -> None:
    repo = StubRepository(repository_name="repo", repository_type=AuditRepositoryType.MEMORY)
    assert repo.validate_audit_id(" A-1 ", operation=AuditRepositoryOperation.READ) == "A-1"
    record = make_record()
    assert repo.validate_record(record, operation=AuditRepositoryOperation.APPEND) is record
    with pytest.raises(AuditInvalidRecordError):
        repo.validate_record(object(), operation=AuditRepositoryOperation.APPEND)
