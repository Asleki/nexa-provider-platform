"""Immutable result returned by registry audit integration."""
from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
from shared.audit import AuditRepositoryResult
from .registry_audit_errors import RegistryAuditResultError

@dataclass(frozen=True, slots=True)
class RegistryAuditResult:
    attempted: bool
    success: bool
    audit_id: str | None = None
    event_id: str | None = None
    event_type: str | None = None
    repository_result: AuditRepositoryResult | None = None
    error_code: str | None = None
    error_type: str | None = None
    message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.attempted,bool) or not isinstance(self.success,bool): raise RegistryAuditResultError("attempted and success must be bool values.")
        if self.success and not self.attempted: raise RegistryAuditResultError("successful audit results must be attempted.")
        if (self.event_id is None)!=(self.event_type is None): raise RegistryAuditResultError("event_id and event_type must be provided together.")
        if self.repository_result is not None and not isinstance(self.repository_result,AuditRepositoryResult): raise RegistryAuditResultError("repository_result must be AuditRepositoryResult.")
        if not isinstance(self.metadata,Mapping): raise RegistryAuditResultError("metadata must be a mapping.")
        object.__setattr__(self,"metadata",MappingProxyType(dict(self.metadata)))
    @classmethod
    def recorded(cls, repository_result, *, event_id=None, event_type=None):
        return cls(True,True,repository_result.audit_id,event_id,event_type,repository_result,message="Registry audit recorded.")
    @classmethod
    def failed(cls, *, error_code, error_type, message, metadata=None):
        return cls(True,False,error_code=error_code,error_type=error_type,message=message,metadata=metadata or {})
    def to_metadata(self):
        value={"audit_attempted":self.attempted,"audit_success":self.success}
        if self.audit_id: value["audit_id"]=self.audit_id
        if self.event_id: value.update({"audit_event_id":self.event_id,"audit_event_type":self.event_type})
        if self.error_code: value.update({"audit_error_code":self.error_code,"audit_error_type":self.error_type,"audit_requires_attention":True})
        return value
__all__=["RegistryAuditResult"]
