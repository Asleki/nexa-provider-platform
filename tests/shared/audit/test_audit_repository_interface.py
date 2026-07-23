import inspect
import pytest
from shared.audit.audit_repository_interface import AuditRepositoryInterface


def test_interface_is_abstract() -> None:
    assert inspect.isabstract(AuditRepositoryInterface)
    with pytest.raises(TypeError):
        AuditRepositoryInterface()


def test_interface_declares_only_append_only_repository_methods() -> None:
    expected = {"repository_name", "repository_type", "append", "get", "list_all", "exists", "count"}
    assert expected.issubset(set(AuditRepositoryInterface.__abstractmethods__))
    assert not hasattr(AuditRepositoryInterface, "delete")
    assert not hasattr(AuditRepositoryInterface, "clear")
    assert not hasattr(AuditRepositoryInterface, "update")
