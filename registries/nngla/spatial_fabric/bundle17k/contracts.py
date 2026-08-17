from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re
_GEO=re.compile(r'^NG-GEO-\d{6}$'); _PARCEL=re.compile(r'^NV-\d{2}-\d{3}-\d{4,}$'); _SURVEY=re.compile(r'^NG-SRV-\d{6}$')
class GeometryChangeNature(str,Enum): CORRECTION='CORRECTION'; PHYSICAL_CHANGE='PHYSICAL_CHANGE'; BOUNDARY_CHANGE='BOUNDARY_CHANGE'; REALIGNMENT='REALIGNMENT'
@dataclass(frozen=True,slots=True)
class GeometryChangeCandidate:
 change_candidate_id:str; subject_type:str; subject_id:str; geometry_role_code:str; current_geometry_id:str; proposed_geometry_reference:str; reserved_geometry_id:str; change_reason_code:str; change_nature:GeometryChangeNature; crs_code:str; survey_id:str; effective_on:str; source_reference:str; runtime_mode:str; runtime_effect_scope:str; status:str
 def __post_init__(self):
  if not self.change_candidate_id.startswith('geochangecand:nngla:'): raise ValueError('invalid geometry change candidate identity')
  if _GEO.fullmatch(self.current_geometry_id) is None: raise ValueError('current geometry id invalid')
  if self.reserved_geometry_id and _GEO.fullmatch(self.reserved_geometry_id) is None: raise ValueError('reserved geometry id invalid')
  if self.reserved_geometry_id==self.current_geometry_id: raise ValueError('new geometry version cannot reuse old geometry id')
  if self.runtime_mode=='simulation' and self.reserved_geometry_id: raise ValueError('Simulation candidate cannot consume sovereign geometry identity')
  if self.crs_code!='NG-CRS-EPSG4326': raise ValueError('governed CRS required')
  if self.survey_id and _SURVEY.fullmatch(self.survey_id) is None: raise ValueError('survey id invalid')
  if self.runtime_mode not in {'simulation','production'} or self.runtime_effect_scope!='RUNTIME_SCOPED': raise ValueError('runtime dimensions invalid')
  if self.status!='CANDIDATE': raise ValueError('change must start as candidate')
@dataclass(frozen=True,slots=True)
class GeometrySupersessionLink:
 link_id:str; subject_id:str; geometry_role_code:str; predecessor_geometry_id:str; successor_geometry_id:str; effective_on:str; change_reason_code:str; survey_id:str; authority_runtime_mode:str; source_reference:str; status:str
 def __post_init__(self):
  if not self.link_id.startswith('geosupersede:nngla:'): raise ValueError('invalid supersession identity')
  if _GEO.fullmatch(self.predecessor_geometry_id) is None or _GEO.fullmatch(self.successor_geometry_id) is None or self.predecessor_geometry_id==self.successor_geometry_id: raise ValueError('invalid geometry supersession ids')
  if self.survey_id and _SURVEY.fullmatch(self.survey_id) is None: raise ValueError('survey id invalid')
  if self.authority_runtime_mode!='production' or self.status!='EFFECTIVE': raise ValueError('canonical supersession requires production authority')
@dataclass(frozen=True,slots=True)
class SurveyObservationCandidate:
 observation_id:str; survey_id:str; subject_id:str; observed_at:str; longitude:float; latitude:float; elevation_m:str; crs_code:str; accuracy_class_code:str; instrument_record_reference:str; surveyor_approval_reference:str; source_reference:str; qualification_status:str
 def __post_init__(self):
  if not self.observation_id.startswith('surveyobs:nngla:') or _SURVEY.fullmatch(self.survey_id) is None: raise ValueError('survey observation identity invalid')
  if not -180<=self.longitude<=180 or not -90<=self.latitude<=90 or self.crs_code!='NG-CRS-EPSG4326': raise ValueError('survey coordinate invalid')
@dataclass(frozen=True,slots=True)
class PhysicalStateChangeCandidate:
 state_change_id:str; subject_type:str; subject_id:str; prior_state:str; proposed_state:str; geometry_change_candidate_id:str; effective_on:str; source_reference:str; runtime_mode:str; status:str
 def __post_init__(self):
  if not self.state_change_id.startswith('physstate:nngla:') or self.prior_state==self.proposed_state: raise ValueError('invalid physical state change')
  if self.runtime_mode not in {'simulation','production'} or self.status!='CANDIDATE': raise ValueError('physical-state runtime/status invalid')
@dataclass(frozen=True,slots=True)
class GeometryChangeQualification:
 qualification_id:str; change_candidate_id:str; subject_identity_stable:bool; successor_identity_new:bool; crs_valid:bool; survey_policy_respected:bool; history_preserved:bool; runtime_authority_valid:bool; status:str; findings:str
__all__=['GeometryChangeNature','GeometryChangeCandidate','GeometrySupersessionLink','SurveyObservationCandidate','PhysicalStateChangeCandidate','GeometryChangeQualification']
