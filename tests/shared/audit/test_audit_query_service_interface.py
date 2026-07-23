import inspect
from shared.audit import AuditQueryServiceInterface

def test_interface_is_abstract():
    assert inspect.isabstract(AuditQueryServiceInterface)

def test_interface_exposes_query():
    assert hasattr(AuditQueryServiceInterface, "query")
