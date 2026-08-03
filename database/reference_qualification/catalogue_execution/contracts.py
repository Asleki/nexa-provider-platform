"""Contracts for M009.13.12 catalogue-plan CLI execution."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

_VALID_RUNTIMES={"production","simulation"}

def _text(value,name):
    if not isinstance(value,str) or not value.strip(): raise ValueError(f"{name} is required.")
    return value.strip()

@dataclass(frozen=True, slots=True)
class CataloguePlanExecutionRequest:
    plan_id:str; runtime_mode:str; sample_size:int; random_seed:int; submitter_actor_id:str|None=None; approver_actor_id:str|None=None; repository_revision:str="unknown"
    def __post_init__(self):
        object.__setattr__(self,"plan_id",_text(self.plan_id,"plan_id"))
        runtime=_text(self.runtime_mode,"runtime_mode").lower()
        if runtime not in _VALID_RUNTIMES: raise ValueError("runtime_mode must be production or simulation.")
        object.__setattr__(self,"runtime_mode",runtime)
        if not isinstance(self.sample_size,int) or isinstance(self.sample_size,bool) or self.sample_size<1: raise ValueError("sample_size must be a positive integer.")
        if not isinstance(self.random_seed,int) or isinstance(self.random_seed,bool): raise ValueError("random_seed must be an integer.")
        if self.submitter_actor_id is not None: object.__setattr__(self,"submitter_actor_id",_text(self.submitter_actor_id,"submitter_actor_id"))
        if self.approver_actor_id is not None: object.__setattr__(self,"approver_actor_id",_text(self.approver_actor_id,"approver_actor_id"))
        if self.submitter_actor_id and self.approver_actor_id and self.submitter_actor_id==self.approver_actor_id: raise ValueError("submitter and approver must be different actors.")
        object.__setattr__(self,"repository_revision",_text(self.repository_revision,"repository_revision"))

@dataclass(frozen=True, slots=True)
class CataloguePlanStepPreview:
    step_id:str; manifest_path:str; file_id:str; target_kind:str; classification:str; source_row_count:int; selected_source_record_ids:tuple[str,...]; selection_fingerprint:str; distribution:Mapping[str,object]

@dataclass(frozen=True, slots=True)
class CataloguePlanPreview:
    plan_id:str; runtime_mode:str; sample_size_per_step:int; random_seed:int; database_name:str; environment:str; repository_revision:str; plan_fingerprint:str; confirmation_token:str; steps:tuple[CataloguePlanStepPreview,...]; expected_candidate_count:int; generated_at:datetime

@dataclass(frozen=True, slots=True)
class CataloguePlanStepReceipt:
    step_id:str; file_id:str; target_kind:str; selected_count:int; validated_count:int; imported_count:int; existing_count:int; quarantined_count:int; rejected_count:int; failed_count:int; profiles_created:int; profiles_existing:int; outcome:str; selection_fingerprint:str

@dataclass(frozen=True, slots=True)
class CataloguePlanExecutionReceipt:
    execution_id:str; plan_id:str; runtime_mode:str; database_name:str; environment:str; repository_revision:str; plan_fingerprint:str; started_at:datetime; completed_at:datetime; status:str; steps:tuple[CataloguePlanStepReceipt,...]
    @property
    def imported_count(self): return sum(x.imported_count for x in self.steps)
    @property
    def existing_count(self): return sum(x.existing_count for x in self.steps)
    @property
    def failed_count(self): return sum(x.failed_count for x in self.steps)
    @property
    def selected_count(self): return sum(x.selected_count for x in self.steps)

__all__=["CataloguePlanExecutionRequest","CataloguePlanStepPreview","CataloguePlanPreview","CataloguePlanStepReceipt","CataloguePlanExecutionReceipt"]
