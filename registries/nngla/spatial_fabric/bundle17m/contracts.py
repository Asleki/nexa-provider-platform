
from __future__ import annotations
from dataclasses import dataclass
import re
_NAME=re.compile(r'^NG-NAM-[A-Z]{3}-\d{6}$')
_ALLOWED_ROLES=frozenset({'PRIMARY','ALTERNATE','HISTORIC','NICKNAME'})
@dataclass(frozen=True,slots=True)
class NameFamilyDefinition:
    name_family_code:str; catalogue_path:str; id_field:str; id_prefix:str; id_pattern:str; sequence_width:int; record_count:int; default_scope_type:str; eligible_subject_family:str; normalization_policy:str; allocation_authority_runtime:str; status:str
    def __post_init__(self):
        if not self.name_family_code or not self.catalogue_path or not self.id_field: raise ValueError('name family source contract incomplete')
        if not self.id_prefix.startswith('NG-NAM-') or self.sequence_width!=6 or self.allocation_authority_runtime!='production' or self.status!='ACTIVE': raise ValueError('name family allocation contract invalid')
@dataclass(frozen=True,slots=True)
class NameReservation:
    reservation_id:str; name_family_code:str; normalized_match_key:str; scope_type:str; scope_reference:str; reserved_name_id:str; idempotency_key:str; authority_runtime_mode:str; reservation_status:str
    def __post_init__(self):
        if not self.reservation_id.startswith('nameres:nngla:'): raise ValueError('name reservation identity invalid')
        if self.reserved_name_id and _NAME.fullmatch(self.reserved_name_id) is None: raise ValueError('reserved name id invalid')
        if self.authority_runtime_mode!='production' or self.reservation_status!='RESERVED': raise ValueError('sovereign name reservation requires production authority')
@dataclass(frozen=True,slots=True)
class NameAssignmentRule:
    rule_set_id:str; name_family_code:str; allowed_assignment_roles:frozenset[str]; requires_recognized_subject:bool; primary_requires_approval:bool; primary_requires_gazette:bool; alternate_allowed:bool; historic_allowed:bool; nickname_allowed:bool; status:str
    def __post_init__(self):
        if not self.rule_set_id.startswith('namerule:nngla:') or not self.allowed_assignment_roles <= _ALLOWED_ROLES or self.status!='ACTIVE': raise ValueError('invalid name assignment rule')
@dataclass(frozen=True,slots=True)
class NameLifecycleTransition:
    transition_id:str; from_status:str; to_status:str; requires_approval:bool; requires_gazette:bool; creates_legal_effect:bool; terminal_transition:bool; status:str
    def __post_init__(self):
        if self.from_status==self.to_status or self.status!='ACTIVE': raise ValueError('invalid name lifecycle transition')
@dataclass(frozen=True,slots=True)
class GazetteActionCandidate:
    candidate_id:str; subject_id:str; name_id:str; gazette_action_code:str; prior_name_id:str; proposed_effective_on:str; proposer_reference:str; decision_reference:str; runtime_mode:str; candidate_status:str
    def __post_init__(self):
        if not self.candidate_id.startswith('gazettecand:nngla:') or self.runtime_mode not in {'simulation','production'}: raise ValueError('gazette candidate contract invalid')
@dataclass(frozen=True,slots=True)
class NameAssignmentResult:
    result_id:str; assignment_candidate_id:str; subject_id:str; name_id:str; canonical_name:str; assignment_role:str; source_assignment_status:str; result_status:str; official_effect:bool; gazette_reference:str; source_basis:str
    def __post_init__(self):
        if not self.result_id.startswith('nameasnresult:nngla:') or self.assignment_role not in _ALLOWED_ROLES: raise ValueError('name assignment result invalid')
        if self.official_effect and not self.gazette_reference: raise ValueError('official legal naming effect requires gazette reference')
__all__=['NameFamilyDefinition','NameReservation','NameAssignmentRule','NameLifecycleTransition','GazetteActionCandidate','NameAssignmentResult']
