"""Normalised and secret-safe registry audit context."""
from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping
from registries.api import RegistryApiRequest
from .registry_audit_errors import RegistryAuditValidationError

_SECRET_FRAGMENTS=("pin","password","passcode","secret","token","api_key","private_key","credential")
def _clean(value):
    if isinstance(value,Mapping): return {str(k):_clean(v) for k,v in value.items() if not any(x in str(k).lower() for x in _SECRET_FRAGMENTS)}
    if isinstance(value,(list,tuple)): return tuple(_clean(v) for v in value)
    return value

def _text(value, fallback):
    return value.strip() if isinstance(value,str) and value.strip() else fallback

@dataclass(frozen=True, slots=True)
class RegistryAuditContext:
    actor_id:str; actor_type:str; runtime_id:str; runtime_mode:str; source:str
    correlation_id:str; causation_id:str|None=None; device_id:str|None=None
    metadata:Mapping[str,Any]=field(default_factory=dict)
    def __post_init__(self):
        for name in ("actor_id","actor_type","runtime_id","runtime_mode","source","correlation_id"):
            value=getattr(self,name)
            if not isinstance(value,str) or not value.strip(): raise RegistryAuditValidationError(f"{name} must be non-empty text.")
            object.__setattr__(self,name,value.strip())
        object.__setattr__(self,"metadata",MappingProxyType(dict(self.metadata)))
    @classmethod
    def from_request(cls, request:RegistryApiRequest):
        if not isinstance(request,RegistryApiRequest): raise RegistryAuditValidationError("request must be RegistryApiRequest.")
        m=dict(request.metadata)
        actor_id=_text(m.get("actor_id"),_text(m.get("simulation_agent_id"),_text(m.get("human_supervisor_id"),"registry-api")))
        actor_type=_text(m.get("actor_type"),"simulation_agent" if m.get("simulation_agent_id") else ("human_supervisor" if m.get("human_supervisor_id") else "system"))
        reserved={"actor_id","actor_type","runtime_id","runtime_mode","source","correlation_id","causation_id","device_id"}
        extra=_clean({k:v for k,v in m.items() if k not in reserved})
        if actor_id=="registry-api": extra["actor_resolution"]="fallback"
        return cls(actor_id,actor_type,_text(m.get("runtime_id"),"registry-runtime-unassigned"),_text(m.get("runtime_mode"),"unspecified"),_text(m.get("source"),"registry_api"),_text(m.get("correlation_id"),request.request_id),m.get("causation_id"),m.get("device_id"),extra)
__all__=["RegistryAuditContext"]
