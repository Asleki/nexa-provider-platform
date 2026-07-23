import inspect
from shared.audit.audit_export_service import AuditExportService
from shared.audit.audit_export_service_interface import AuditExportServiceInterface


def test_interface_is_abstract() -> None:
    assert inspect.isabstract(AuditExportServiceInterface)


def test_service_implements_interface() -> None:
    assert issubclass(AuditExportService, AuditExportServiceInterface)
