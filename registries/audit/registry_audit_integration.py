"""Registry audit adapter backed by the shared append-only audit repository."""
from __future__ import annotations
from registries.ports.registry_audit_port import RegistryAuditPort
from shared.audit import AuditError, AuditRepositoryInterface
from .registry_audit_errors import RegistryAuditConfigurationError
from .registry_audit_record_factory import RegistryAuditRecordFactory
from .registry_audit_result import RegistryAuditResult
class RegistryAuditIntegration(RegistryAuditPort):
    def __init__(self,repository:AuditRepositoryInterface,*,record_factory=None):
        if not isinstance(repository,AuditRepositoryInterface): raise RegistryAuditConfigurationError("repository must implement AuditRepositoryInterface.")
        self.repository=repository; self.record_factory=record_factory or RegistryAuditRecordFactory()
    def record(self,*,request,response):
        try:
            record=self.record_factory.create(request,response); result=self.repository.append(record)
            return RegistryAuditResult.recorded(result,event_id=record.event_id,event_type=record.event_type)
        except Exception as exc:
            code=getattr(exc,"error_code","NPP-REGISTRY-AUDIT-030")
            return RegistryAuditResult.failed(error_code=code,error_type=type(exc).__name__,message="Registry audit could not be recorded.",metadata={"cause":type(exc).__name__})
__all__=["RegistryAuditIntegration"]
