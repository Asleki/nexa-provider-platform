from __future__ import annotations
from ._shared import stable_id
from .contracts import GeometryChangeCandidate,GeometryChangeNature,GeometrySupersessionLink,PhysicalStateChangeCandidate

def form_geometry_change_candidate(*,subject_type,subject_id,geometry_role_code,current_geometry_id,proposed_geometry_reference,change_reason_code,change_nature,source_reference,runtime_mode='simulation',survey_id='',effective_on='',reserved_geometry_id=''):
 cid=stable_id('geochangecand:nngla:',subject_type,subject_id,current_geometry_id,proposed_geometry_reference,change_reason_code,source_reference)
 return GeometryChangeCandidate(cid,subject_type,subject_id,geometry_role_code,current_geometry_id,proposed_geometry_reference,reserved_geometry_id,change_reason_code,GeometryChangeNature(change_nature),'NG-CRS-EPSG4326',survey_id,effective_on,source_reference,runtime_mode,'RUNTIME_SCOPED','CANDIDATE')
def bind_reserved_geometry(candidate,reserved_geometry_id):
 return GeometryChangeCandidate(candidate.change_candidate_id,candidate.subject_type,candidate.subject_id,candidate.geometry_role_code,candidate.current_geometry_id,candidate.proposed_geometry_reference,reserved_geometry_id,candidate.change_reason_code,candidate.change_nature,candidate.crs_code,candidate.survey_id,candidate.effective_on,candidate.source_reference,candidate.runtime_mode,candidate.runtime_effect_scope,candidate.status)
def form_supersession(candidate,*,authority_runtime_mode='production'):
 if not candidate.reserved_geometry_id: raise ValueError('successor geometry id must be reserved first')
 if candidate.runtime_mode!='production': raise ValueError('canonical supersession requires production candidate')
 lid=stable_id('geosupersede:nngla:',candidate.subject_id,candidate.current_geometry_id,candidate.reserved_geometry_id,candidate.effective_on)
 return GeometrySupersessionLink(lid,candidate.subject_id,candidate.geometry_role_code,candidate.current_geometry_id,candidate.reserved_geometry_id,candidate.effective_on,candidate.change_reason_code,candidate.survey_id,authority_runtime_mode,candidate.source_reference,'EFFECTIVE')
def form_physical_state_change(*,subject_type,subject_id,prior_state,proposed_state,source_reference,runtime_mode='simulation',geometry_change_candidate_id='',effective_on=''):
 sid=stable_id('physstate:nngla:',subject_type,subject_id,prior_state,proposed_state,effective_on,source_reference)
 return PhysicalStateChangeCandidate(sid,subject_type,subject_id,prior_state,proposed_state,geometry_change_candidate_id,effective_on,source_reference,runtime_mode,'CANDIDATE')
__all__=['form_geometry_change_candidate','bind_reserved_geometry','form_supersession','form_physical_state_change']
