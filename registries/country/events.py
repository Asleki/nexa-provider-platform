"""P006.7.1.8 Country Registry domain events and audit coupling."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4
from shared.events.base_event import BaseEvent
from shared.events.event_metadata import EventMetadata
from shared.audit.audit_action import AuditAction
from shared.audit.audit_outcome import AuditOutcome
from shared.audit.audit_record import AuditRecord
from shared.runtime.operation_runtime import OperationRuntimeMode

class CountryEventType(str,Enum):
    COUNTRY_REGISTERED="COUNTRY_REGISTERED"
    COUNTRY_REPLACED="COUNTRY_REPLACED"
    COUNTRY_QUALIFIED="COUNTRY_QUALIFIED"

class CountryEvent(BaseEvent):
    def __init__(self,*,event_id,event_type,occurred_at,country_id,record_version,runtime_mode,metadata,payload=None):
        runtime=runtime_mode if isinstance(runtime_mode,OperationRuntimeMode) else OperationRuntimeMode(str(runtime_mode).lower())
        et=event_type if isinstance(event_type,CountryEventType) else CountryEventType(str(event_type))
        if not isinstance(country_id,str) or not country_id.startswith("country:"): raise ValueError("country_id must use the country: namespace.")
        if not isinstance(record_version,int) or isinstance(record_version,bool) or record_version<1: raise ValueError("record_version must be positive.")
        if not isinstance(metadata,EventMetadata): raise TypeError("metadata must be EventMetadata.")
        full={"country_id":country_id.lower(),"record_version":record_version,"runtime_mode":runtime.value}; full.update(dict(payload or {}))
        super().__init__(event_id=event_id,event_type=et.value,event_version=1,occurred_at=occurred_at,metadata=metadata.to_dict(),payload=full)
        self.country_id=country_id.lower(); self.record_version=record_version; self.runtime_mode=runtime

@dataclass(frozen=True,slots=True)
class CountryMutationTrace:
    event: CountryEvent
    audit: AuditRecord

class CountryEventFactory:
    @staticmethod
    def create(*,event_type,country_id,record_version,runtime_mode,correlation_id,actor_id,device_id=None,causation_id=None,occurred_at=None,payload=None)->CountryMutationTrace:
        when=occurred_at or datetime.now(timezone.utc)
        runtime=runtime_mode if isinstance(runtime_mode,OperationRuntimeMode) else OperationRuntimeMode(str(runtime_mode).lower())
        meta=EventMetadata(correlation_id=correlation_id,causation_id=causation_id,actor_id=actor_id,device_id=device_id,source="country_registry")
        event=CountryEvent(event_id=f"country-event:{uuid4()}",event_type=event_type,occurred_at=when,country_id=country_id,record_version=record_version,runtime_mode=runtime,metadata=meta,payload=payload)
        action=AuditAction.REGISTER if event.event_type==CountryEventType.COUNTRY_REGISTERED.value else (AuditAction.VALIDATE if event.event_type==CountryEventType.COUNTRY_QUALIFIED.value else AuditAction.UPDATE)
        audit=AuditRecord(audit_id=f"audit:{uuid4()}",version=1,recorded_at=when,action=action,outcome=AuditOutcome.SUCCESS,actor_id=actor_id,actor_type="country_registry_actor",target_namespace="country",target_type="country_registry_record",target_id=country_id,runtime_id="realm:nexilabs:novegeo",runtime_mode=runtime.value,source="country_registry",event_id=event.event_id,event_type=event.event_type,correlation_id=correlation_id,causation_id=causation_id,device_id=device_id,metadata={"record_version":record_version})
        return CountryMutationTrace(event,audit)

__all__=["CountryEventType","CountryEvent","CountryMutationTrace","CountryEventFactory"]
