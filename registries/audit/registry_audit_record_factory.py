"""Factory adapting Registry API facts into canonical shared AuditRecord objects."""
from __future__ import annotations
from collections.abc import Callable
from datetime import datetime,timezone
from uuid import uuid4
from registries.api import RegistryApiRequest, RegistryApiResponse
from shared.audit import AuditRecord
from .registry_audit_context import RegistryAuditContext
from .registry_audit_errors import RegistryAuditConfigurationError
from .registry_audit_policy import RegistryAuditPolicy

class RegistryAuditRecordFactory:
    def __init__(self,*,policy=None,clock=None,audit_id_factory=None):
        self.policy=policy or RegistryAuditPolicy(); self._clock=clock or (lambda:datetime.now(timezone.utc)); self._ids=audit_id_factory or (lambda:f"AUD-{uuid4()}")
    def create(self,request:RegistryApiRequest,response:RegistryApiResponse):
        context=RegistryAuditContext.from_request(request); target_type,target_id=self.policy.target_for(request)
        event=response.events[0] if response.events else None
        metadata=dict(context.metadata); metadata.update({"registry_operation":request.operation.value,"api_success":response.success})
        if response.error: metadata["registry_error"]={k:v for k,v in response.error.items() if k!="message"}
        now=self._clock()
        if not isinstance(now,datetime) or now.tzinfo is None: raise RegistryAuditConfigurationError("clock must return timezone-aware datetime.")
        audit_id=self._ids()
        return AuditRecord(audit_id=audit_id,version=1,recorded_at=now,action=self.policy.action_for(request.operation),outcome=self.policy.outcome_for(response),actor_id=context.actor_id,actor_type=context.actor_type,target_namespace="registries",target_type=target_type,target_id=target_id,runtime_id=context.runtime_id,runtime_mode=context.runtime_mode,source=context.source,event_id=None if event is None else event.event_id,event_type=None if event is None else event.event_type,correlation_id=context.correlation_id,causation_id=context.causation_id,request_id=request.request_id,device_id=context.device_id,metadata=metadata)
__all__=["RegistryAuditRecordFactory"]
