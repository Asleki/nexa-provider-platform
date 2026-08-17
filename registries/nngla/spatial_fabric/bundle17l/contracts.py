
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re
_FEATURE=re.compile(r'^NG-FEAT-\d{6}$')
class RecognitionDisposition(str,Enum):
    REUSE_CANONICAL='REUSE_CANONICAL'; RECOGNIZE_NEW='RECOGNIZE_NEW'; DEFER='DEFER'; REJECT='REJECT'
@dataclass(frozen=True,slots=True)
class FeatureQualificationRule:
    rule_set_id:str; feature_type_code:str; engine_domain:str; geometry_expectation:str; requires_physical_observation:bool; requires_geometry:bool; requires_spatial_qualification:bool; requires_environment_qualification:bool; requires_conflict_qualification:bool; existing_canonical_reuse_allowed:bool; simulation_may_form_candidate:bool; production_recognition_required:bool; allow_reclassification_same_identity:bool; allow_retirement_without_delete:bool; status:str
    def __post_init__(self):
        if not self.rule_set_id.startswith('featrule:nngla:'): raise ValueError('invalid feature rule identity')
        if self.engine_domain!='PHYSICAL_FEATURE_RECOGNITION' or self.status!='ACTIVE': raise ValueError('invalid feature rule domain/status')
        if not self.feature_type_code or not self.geometry_expectation: raise ValueError('feature type/geometry expectation required')
@dataclass(frozen=True,slots=True)
class FeatureCandidate:
    candidate_id:str; source_feature_id:str; feature_type_code:str; source_dataset_id:str; source_record_reference:str; physical_origin_class:str; geometry_reference:str; geometry_status:str; qualification_status:str; existing_canonical_feature_id:str; runtime_mode:str; runtime_effect_scope:str; candidate_status:str
    def __post_init__(self):
        if not self.candidate_id.startswith('featcand:nngla:'): raise ValueError('candidate identity invalid')
        if self.physical_origin_class!='NATURAL': raise ValueError('17L only handles natural physical features')
        if self.existing_canonical_feature_id and _FEATURE.fullmatch(self.existing_canonical_feature_id) is None: raise ValueError('canonical feature id invalid')
        if self.runtime_mode not in {'simulation','production'}: raise ValueError('runtime mode invalid')
        if self.runtime_effect_scope not in {'SHARED_REFERENCE','SIMULATION_ONLY','PRODUCTION_ONLY','RUNTIME_SCOPED'}: raise ValueError('effect scope invalid')
@dataclass(frozen=True,slots=True)
class ObservationLink:
    link_id:str; candidate_id:str; observation_type:str; source_dataset_id:str; source_record_id:str; source_path_reference:str; source_sha256:str; evidence_status:str
    def __post_init__(self):
        if not self.link_id.startswith('featobs:nngla:') or not self.candidate_id.startswith('featcand:nngla:'): raise ValueError('observation link identity invalid')
@dataclass(frozen=True,slots=True)
class FeatureRecognitionResult:
    result_id:str; candidate_id:str; feature_type_code:str; disposition:RecognitionDisposition; canonical_feature_id:str; qualified:bool; production_authority_required:bool; geometry_ready:bool; history_preserved:bool; result_status:str; findings:str
    def __post_init__(self):
        if not self.result_id.startswith('featresult:nngla:'): raise ValueError('result identity invalid')
        if self.canonical_feature_id and _FEATURE.fullmatch(self.canonical_feature_id) is None: raise ValueError('canonical feature id invalid')
        if self.disposition is RecognitionDisposition.REUSE_CANONICAL and not self.canonical_feature_id: raise ValueError('canonical reuse requires existing identity')
@dataclass(frozen=True,slots=True)
class FeatureLifecycleTransition:
    transition_id:str; from_status:str; to_status:str; requires_production_authority:bool; retains_feature_identity:bool; terminal_transition:bool; status:str
    def __post_init__(self):
        if self.from_status==self.to_status or not self.retains_feature_identity or self.status!='ACTIVE': raise ValueError('invalid lifecycle transition')
__all__=['RecognitionDisposition','FeatureQualificationRule','FeatureCandidate','ObservationLink','FeatureRecognitionResult','FeatureLifecycleTransition']
