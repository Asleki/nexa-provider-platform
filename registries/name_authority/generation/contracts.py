"""M009.12 Bundle C generation contracts."""
from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from collections.abc import Mapping, Sequence
import hashlib, json, re
from registries.names import CanonicalName, NameKind, NameStatus

_ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
def _utcnow(): return datetime.now(timezone.utc)
def _freeze(v):
    if isinstance(v,Mapping): return MappingProxyType({str(k):_freeze(x) for k,x in v.items()})
    if isinstance(v,(list,tuple)): return tuple(_freeze(x) for x in v)
    return v

class SimulationNameGenerationFamily(str,Enum):
    NOVEGEO_NATIVE_TWO_PART="novegeo_native_two_part"
    NOVEGEO_NATIVE_THREE_PART="novegeo_native_three_part"
    MULTICULTURAL_TWO_PART="multicultural_two_part"
    MULTICULTURAL_THREE_PART="multicultural_three_part"
    IMMIGRATION_APPROVED_PAIR="immigration_approved_pair"
    ACCENTED_TWO_PART="accented_two_part"
    APPROVED_MIXED_ORIGIN="approved_mixed_origin"
    @classmethod
    def parse(cls,v): return v if isinstance(v,cls) else cls(str(v).strip().lower())

class GenerationBatchStatus(str,Enum):
    DRAFT="draft"; VALIDATED="validated"; READY="ready"; RUNNING="running"; PAUSED="paused"; COMPLETED="completed"; FAILED="failed"; CANCELLED="cancelled"; EXHAUSTED="exhausted"
    @classmethod
    def parse(cls,v): return v if isinstance(v,cls) else cls(str(v).strip().lower())

class GenerationResultOutcome(str,Enum): INSERTED="inserted"; EXISTING="existing"; SKIPPED="skipped"; FAILED="failed"

@dataclass(frozen=True,slots=True)
class AtomicNameGenerationProfile:
    name_id:str; canonical_value:str; name_kind:NameKind; runtime_mode:str; source_family:str="unknown"; sex_usage:str="unspecified"; source_pair_key:str|None=None; metadata:Mapping[str,object]=field(default_factory=dict)
    def __post_init__(self):
        if not _ID.fullmatch(self.name_id): raise ValueError("name_id is invalid.")
        object.__setattr__(self,"name_kind",NameKind.parse(self.name_kind))
        if self.runtime_mode!="simulation": raise ValueError("generation profiles must be simulation-scoped.")
        object.__setattr__(self,"metadata",_freeze(self.metadata))
    @classmethod
    def from_canonical(cls,name:CanonicalName):
        if name.metadata.status is not NameStatus.ACTIVE or name.metadata.runtime_mode!="simulation": raise ValueError("only active simulation names may enter a generation snapshot.")
        attrs=dict(name.metadata.attributes); seed=dict(attrs.get("seed",{})) if isinstance(attrs.get("seed",{}),Mapping) else {}
        pair=None
        if seed.get("source_pair_id"):
            pair="|".join(str(seed.get(k,"")) for k in ("dataset_id","file_id","source_pair_id"))
        return cls(name.name_id,name.canonical_value,name.name_kind,"simulation",str(seed.get("source_family","unknown")),str(seed.get("sex_usage",attrs.get("sex_usage","unspecified"))),pair,seed)

@dataclass(frozen=True,slots=True)
class GenerationSourceSnapshot:
    snapshot_id:str; runtime_mode:str; members:tuple[AtomicNameGenerationProfile,...]; checksum:str; created_at:datetime=field(default_factory=_utcnow)
    def __post_init__(self):
        if self.runtime_mode!="simulation": raise ValueError("source snapshots must use simulation runtime.")
        ordered=tuple(sorted(self.members,key=lambda x:(x.name_kind.value,x.name_id)))
        if len({x.name_id for x in ordered})!=len(ordered): raise ValueError("snapshot members must be unique.")
        object.__setattr__(self,"members",ordered)
        expected=self.calculate_checksum(ordered)
        if self.checksum!=expected: raise ValueError("source snapshot checksum mismatch.")
    @staticmethod
    def calculate_checksum(members):
        payload=[{"id":x.name_id,"kind":x.name_kind.value,"value":x.canonical_value,"runtime":x.runtime_mode,"family":x.source_family,"sex":x.sex_usage,"pair":x.source_pair_key} for x in members]
        return hashlib.sha256(json.dumps(payload,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()).hexdigest()
    @classmethod
    def create(cls,snapshot_id,names):
        members=tuple(x if isinstance(x,AtomicNameGenerationProfile) else AtomicNameGenerationProfile.from_canonical(x) for x in names)
        return cls(snapshot_id,"simulation",members,cls.calculate_checksum(sorted(members,key=lambda x:(x.name_kind.value,x.name_id))))
    def by_kind(self,kind): return tuple(x for x in self.members if x.name_kind is NameKind.parse(kind))

@dataclass(frozen=True,slots=True)
class GenerationFamilyTarget:
    family:SimulationNameGenerationFamily; requested_count:int
    def __post_init__(self):
        object.__setattr__(self,"family",SimulationNameGenerationFamily.parse(self.family))
        if self.requested_count<0: raise ValueError("requested_count cannot be negative.")

@dataclass(frozen=True,slots=True)
class SimulationGenerationRequest:
    generation_batch_id:str; source_snapshot_id:str; source_snapshot_checksum:str; targets:tuple[GenerationFamilyTarget,...]; random_seed:str; batch_size:int=2000; generator_algorithm:str="indexed-sha256-v1"; generator_version:int=1; rules_version:int=1; runtime_mode:str="simulation"
    def __post_init__(self):
        if self.runtime_mode!="simulation": raise ValueError("founding-pool generation is simulation-only.")
        if not _ID.fullmatch(self.generation_batch_id) or not _ID.fullmatch(self.source_snapshot_id): raise ValueError("generation identity is invalid.")
        if not self.random_seed: raise ValueError("random_seed is required.")
        if self.batch_size<1 or self.batch_size>10000: raise ValueError("batch_size must be between 1 and 10000.")
        object.__setattr__(self,"targets",tuple(self.targets))
        if len({x.family for x in self.targets})!=len(self.targets): raise ValueError("generation families must be unique.")
    @property
    def requested_count(self): return sum(x.requested_count for x in self.targets)

@dataclass(frozen=True,slots=True)
class GenerationCapacity:
    family:SimulationNameGenerationFamily; raw_capacity:int; eligible_capacity:int; requested_count:int
    @property
    def is_sufficient(self): return self.eligible_capacity>=self.requested_count

@dataclass(frozen=True,slots=True)
class GenerationBatch:
    generation_batch_id:str; request:SimulationGenerationRequest; status:GenerationBatchStatus=GenerationBatchStatus.DRAFT; next_sequence:int=0; attempted_count:int=0; inserted_count:int=0; existing_count:int=0; skipped_count:int=0; failed_count:int=0; checkpoint_sequence:int=0; created_at:datetime=field(default_factory=_utcnow); completed_at:datetime|None=None; result_checksum:str|None=None; row_version:int=1
    def __post_init__(self): object.__setattr__(self,"status",GenerationBatchStatus.parse(self.status))
    def transition(self,status):
        status=GenerationBatchStatus.parse(status)
        allowed={GenerationBatchStatus.DRAFT:{GenerationBatchStatus.VALIDATED},GenerationBatchStatus.VALIDATED:{GenerationBatchStatus.READY},GenerationBatchStatus.READY:{GenerationBatchStatus.RUNNING,GenerationBatchStatus.CANCELLED},GenerationBatchStatus.RUNNING:{GenerationBatchStatus.PAUSED,GenerationBatchStatus.COMPLETED,GenerationBatchStatus.FAILED,GenerationBatchStatus.CANCELLED,GenerationBatchStatus.EXHAUSTED},GenerationBatchStatus.PAUSED:{GenerationBatchStatus.RUNNING,GenerationBatchStatus.CANCELLED}}
        if status not in allowed.get(self.status,set()): raise ValueError("invalid generation batch transition.")
        return replace(self,status=status,row_version=self.row_version+1,completed_at=_utcnow() if status is GenerationBatchStatus.COMPLETED else self.completed_at)

@dataclass(frozen=True,slots=True)
class GenerationResult:
    generation_batch_id:str; generation_sequence:int; family:SimulationNameGenerationFamily; authority_name_id:str; composition_key:str; outcome:GenerationResultOutcome
    def __post_init__(self):
        object.__setattr__(self,"family",SimulationNameGenerationFamily.parse(self.family)); object.__setattr__(self,"outcome",self.outcome if isinstance(self.outcome,GenerationResultOutcome) else GenerationResultOutcome(self.outcome))
        if self.generation_sequence<0: raise ValueError("generation_sequence cannot be negative.")

@dataclass(frozen=True,slots=True)
class GenerationCheckpoint:
    checkpoint_id:str; generation_batch_id:str; checkpoint_sequence:int; first_generation_sequence:int; last_generation_sequence:int; next_generation_sequence:int; attempted_count:int; inserted_count:int; existing_count:int; skipped_count:int; failed_count:int; batch_checksum:str; source_snapshot_checksum:str; committed_at:datetime=field(default_factory=_utcnow)

@dataclass(frozen=True,slots=True)
class GenerationBatchCommit:
    batch:GenerationBatch; results:tuple[GenerationResult,...]; checkpoint:GenerationCheckpoint
