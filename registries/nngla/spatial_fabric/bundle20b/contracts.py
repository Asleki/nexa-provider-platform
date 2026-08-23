"""Stable physical-feature refinement and naming contracts."""
from __future__ import annotations
from dataclasses import dataclass
import re
_FEAT=re.compile(r'^NG-FEAT-\d{6}$'); _GEO=re.compile(r'^NG-GEO-\d{6}$'); _NAM=re.compile(r'^NG-NAM-[A-Z]{3}-\d{6}$')

@dataclass(frozen=True,slots=True)
class HydroRelationship:
    relationship_id:str; subject_feature_id:str; subject_physical_id:str; relationship_type:str; object_id:str; evidence_basis:str
    def __post_init__(self):
        if not self.relationship_id.startswith('hydrorel:nngla:') or not _FEAT.fullmatch(self.subject_feature_id): raise ValueError('invalid hydro relationship identity')
        if self.relationship_type not in {'MEMBER_OF_DRAINAGE_NETWORK','RECEIVES_TRIBUTARY_AT','FLOWS_TO_COAST','CLOSED_BASIN','CROSSED_BY_ROAD'}: raise ValueError('unsupported hydro relationship')

@dataclass(frozen=True,slots=True)
class LandformExtentCandidate:
    feature_id:str; physical_subject_id:str; existing_geometry_id:str; landform_type:str; polygon:tuple[tuple[float,float],...]; terrain_sample_count:int; geometry_reservation_key:str; source_basis:str
    def __post_init__(self):
        if not _FEAT.fullmatch(self.feature_id) or not _GEO.fullmatch(self.existing_geometry_id): raise ValueError('invalid landform identity chain')
        if len(self.polygon)<4 or self.polygon[0]!=self.polygon[-1] or self.terrain_sample_count<3: raise ValueError('invalid landform extent')
        if not self.geometry_reservation_key.startswith('p006.7.11.13:landform-extent:'): raise ValueError('invalid extent reservation key')

@dataclass(frozen=True,slots=True)
class PhysicalFeatureName:
    feature_id:str; physical_subject_id:str; name_id:str; canonical_name:str; name_family:str; naming_status_code:str; assignment_candidate_id:str; official_effect:bool
    def __post_init__(self):
        if not _FEAT.fullmatch(self.feature_id) or not _NAM.fullmatch(self.name_id): raise ValueError('invalid feature/name identity')
        if self.naming_status_code!='PROPOSED' or self.official_effect: raise ValueError('Bundle 20B preserves proposals; it does not auto-gazette')
