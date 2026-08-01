"""Production manual-name contracts for M009.12 Bundle B."""
from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from collections.abc import Mapping
import re, unicodedata
from registries.names import NameKind, normalize_name_value, comparison_key
from registries.names.name_sex_usage import NameSexUsage

_ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
class ReferenceKnowledgeState(str,Enum):
    KNOWN_REFERENCE="known_reference"; DECLARED_NEW="declared_new"; IMAGINARY="imaginary"; UNKNOWN="unknown"; UNSPECIFIED="unspecified"
    @classmethod
    def parse(cls,v): return v if isinstance(v,cls) else cls(str(v).strip().lower())
class ReferenceBindingState(str,Enum):
    NOT_APPLICABLE="not_applicable"; UNRESOLVED="unresolved"; RESOLVED="resolved"; RETIRED_REFERENCE="retired_reference"
    @classmethod
    def parse(cls,v): return v if isinstance(v,cls) else cls(str(v).strip().lower())
class ManualNameCandidateStatus(str,Enum):
    DRAFT="draft"; SUBMITTED="submitted"; VALIDATED="validated"; QUARANTINED="quarantined"; APPROVED="approved"; REJECTED="rejected"; CANCELLED="cancelled"
    @classmethod
    def parse(cls,v): return v if isinstance(v,cls) else cls(str(v).strip().lower())
class ManualNameApprovalOutcome(str,Enum):
    CREATED_NEW_CANONICAL_NAME="created_new_canonical_name"; REUSED_EXISTING_CANONICAL_NAME="reused_existing_canonical_name"; QUARANTINED="quarantined"; REJECTED="rejected"; CANCELLED="cancelled"

@dataclass(frozen=True,slots=True)
class ReferenceDeclaration:
    knowledge_state: ReferenceKnowledgeState=ReferenceKnowledgeState.UNSPECIFIED
    binding_state: ReferenceBindingState=ReferenceBindingState.NOT_APPLICABLE
    label: str|None=None; reference_id: str|None=None
    def __post_init__(self):
        object.__setattr__(self,"knowledge_state",ReferenceKnowledgeState.parse(self.knowledge_state)); object.__setattr__(self,"binding_state",ReferenceBindingState.parse(self.binding_state))
        label=self.label.strip() if isinstance(self.label,str) else self.label; ref=self.reference_id.strip() if isinstance(self.reference_id,str) else self.reference_id
        object.__setattr__(self,"label",label or None); object.__setattr__(self,"reference_id",ref or None)
        if self.knowledge_state is ReferenceKnowledgeState.KNOWN_REFERENCE:
            if not ref or self.binding_state is not ReferenceBindingState.RESOLVED: raise ValueError("known references require a resolved reference_id.")
        elif self.knowledge_state in (ReferenceKnowledgeState.DECLARED_NEW,ReferenceKnowledgeState.IMAGINARY):
            if not label or ref is not None or self.binding_state not in (ReferenceBindingState.UNRESOLVED,ReferenceBindingState.NOT_APPLICABLE): raise ValueError("declared or imaginary references require a label without a resolved id.")
        elif ref is not None: raise ValueError("unknown or unspecified declarations cannot contain a reference_id.")

@dataclass(frozen=True,slots=True)
class ActorContext:
    actor_id:str; actor_type:str; source:str="name_authority"; correlation_id:str|None=None; device_id:str|None=None
    def __post_init__(self):
        for n in ("actor_id","actor_type","source"):
            v=getattr(self,n)
            if not isinstance(v,str) or not v.strip(): raise ValueError(f"{n} is required.")
            object.__setattr__(self,n,v.strip())

@dataclass(frozen=True,slots=True)
class ProductionManualNameRequest:
    request_id:str; operation_id:str; raw_name_value:str; requested_name_kind:NameKind; sex_usage:NameSexUsage
    actor:ActorContext; origin:ReferenceDeclaration=field(default_factory=ReferenceDeclaration); language:ReferenceDeclaration=field(default_factory=ReferenceDeclaration); community:ReferenceDeclaration=field(default_factory=ReferenceDeclaration)
    script_code:str|None=None; notes:str|None=None; runtime_mode:str="production"; schema_version:int=1; submitted_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc))
    def __post_init__(self):
        for n in ("request_id","operation_id"):
            v=getattr(self,n)
            if not isinstance(v,str) or not _ID.fullmatch(v.strip()): raise ValueError(f"{n} is invalid.")
            object.__setattr__(self,n,v.strip())
        if str(self.runtime_mode).strip().lower()!="production": raise ValueError("manual name introduction requires production runtime.")
        object.__setattr__(self,"runtime_mode","production"); object.__setattr__(self,"requested_name_kind",NameKind.parse(self.requested_name_kind)); object.__setattr__(self,"sex_usage",NameSexUsage.parse(self.sex_usage))
        object.__setattr__(self,"raw_name_value",normalize_name_value(self.raw_name_value))
        if self.submitted_at.tzinfo is None: raise ValueError("submitted_at must be timezone-aware.")

@dataclass(frozen=True,slots=True)
class ManualNameCandidate:
    candidate_id:str; request:ProductionManualNameRequest; status:ManualNameCandidateStatus=ManualNameCandidateStatus.SUBMITTED
    canonical_name_id:str|None=None; reviewed_by_actor_id:str|None=None; reviewed_at:datetime|None=None; decision_reason:str|None=None
    def __post_init__(self):
        if not _ID.fullmatch(self.candidate_id): raise ValueError("candidate_id is invalid.")
        object.__setattr__(self,"status",ManualNameCandidateStatus.parse(self.status))
    @property
    def search_value(self): return comparison_key(self.request.raw_name_value)
    @property
    def identity_key(self): return ("production",self.request.requested_name_kind.value,self.search_value)

@dataclass(frozen=True,slots=True)
class ManualNameValidation:
    is_valid:bool; requires_review:bool; findings:tuple[str,...]=()

@dataclass(frozen=True,slots=True)
class ManualNameApprovalResult:
    candidate:ManualNameCandidate; outcome:ManualNameApprovalOutcome; canonical_name_id:str|None
