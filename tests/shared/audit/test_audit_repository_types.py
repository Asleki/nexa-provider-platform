from shared.audit.audit_repository_types import AuditRepositoryOperation, AuditRepositoryType


def test_operations_are_stable_string_enums() -> None:
    assert [item.value for item in AuditRepositoryOperation] == ["append", "read", "list", "exists", "count"]
    assert all(isinstance(item, str) for item in AuditRepositoryOperation)


def test_repository_type_starts_with_memory() -> None:
    assert AuditRepositoryType.MEMORY.value == "memory"


def test_append_only_contract_excludes_mutating_operations() -> None:
    names = {item.name for item in AuditRepositoryOperation}
    assert names.isdisjoint({"UPDATE", "DELETE", "CLEAR"})
