"""Application contracts for M009.12 Bundle D."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from collections.abc import Mapping
import hashlib, json

class NameAuthorityOperation(str, Enum):
    SEARCH="search"; GET="get"; STATISTICS="statistics"; SUBMIT_MANUAL="submit_manual"; APPROVE_MANUAL="approve_manual"; COMPOSE="compose"; SNAPSHOT="snapshot"; CHANGES="changes"; ACK_SYNC="ack_sync"

class ApplicationErrorCode(str, Enum):
    AUTHENTICATION_REQUIRED="authentication_required"; PERMISSION_DENIED="permission_denied"; RUNTIME_ACCESS_DENIED="runtime_access_denied"; INVALID_REQUEST="invalid_request"; INVALID_CURSOR="invalid_cursor"; NOT_FOUND="not_found"; CONFLICT="conflict"; STALE_VERSION="stale_version"; IDEMPOTENCY_CONFLICT="idempotency_conflict"; SELF_APPROVAL_PROHIBITED="self_approval_prohibited"; OFFLINE_OPERATION_NOT_ALLOWED="offline_operation_not_allowed"; INTERNAL_FAILURE="internal_failure"

@dataclass(frozen=True, slots=True)
class ApplicationPrincipal:
    actor_id:str; actor_type:str; device_id:str; permissions:frozenset[str]; allowed_runtimes:frozenset[str]; authenticated:bool=True; session_reference:str|None=None
    def __post_init__(self):
        for n in ("actor_id","actor_type","device_id"):
            if not str(getattr(self,n)).strip(): raise ValueError(f"{n} is required.")
        object.__setattr__(self,"permissions",frozenset(str(x) for x in self.permissions)); object.__setattr__(self,"allowed_runtimes",frozenset(str(x).lower() for x in self.allowed_runtimes))

@dataclass(frozen=True, slots=True)
class ApplicationRequestContext:
    request_id:str; correlation_id:str; authority_runtime:str; execution_mode:str; principal:ApplicationPrincipal; idempotency_key:str|None=None; expected_version:str|None=None; requested_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))
    def __post_init__(self):
        if self.authority_runtime not in ("production","simulation"): raise ValueError("authority_runtime is invalid.")
        if self.requested_at.tzinfo is None: raise ValueError("requested_at must be timezone-aware.")

@dataclass(frozen=True, slots=True)
class ApplicationError:
    code:ApplicationErrorCode; message:str; retryable:bool=False; field_errors:Mapping[str,str]=field(default_factory=dict)
    def __post_init__(self): object.__setattr__(self,"field_errors",MappingProxyType(dict(self.field_errors)))

@dataclass(frozen=True, slots=True)
class ApplicationResponse:
    ok:bool; request_id:str; correlation_id:str; runtime_mode:str; data:object|None=None; error:ApplicationError|None=None

@dataclass(frozen=True, slots=True)
class ApplicationCommandReceipt:
    idempotency_key:str; operation:NameAuthorityOperation; actor_id:str; runtime_mode:str; request_hash:str; response:ApplicationResponse; created_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))

def stable_request_hash(operation:NameAuthorityOperation, payload:Mapping[str,object])->str:
    raw=json.dumps({"operation":operation.value,"payload":payload},sort_keys=True,separators=(",",":"),default=str,ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()
