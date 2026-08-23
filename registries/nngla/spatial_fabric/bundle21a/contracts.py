"""Publication and projection contracts that keep canonical identity separate from public visibility."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json

@dataclass(frozen=True,slots=True)
class PublicationCandidate:
    subject_id:str; record_family:str; display_name:str; geometry_reference:str; naming_status:str; lifecycle_status:str; spatial_status:str; geometry_publication_status:str
    def __post_init__(self):
        if self.record_family not in {'PLACE','ADMINISTRATIVE_AREA','ROAD','GEOGRAPHIC_FEATURE'}: raise ValueError('unsupported public family')
        if not self.subject_id or not self.display_name: raise ValueError('subject and display name required')

@dataclass(frozen=True,slots=True)
class PublicationDecision:
    subject_id:str; record_family:str; decision:str; reasons:tuple[str,...]; map_renderable:bool; publication_id:str=''
    def __post_init__(self):
        if self.decision not in {'PUBLIC','BLOCKED'}: raise ValueError('invalid publication decision')
        if self.decision=='PUBLIC' and (self.reasons or not self.publication_id): raise ValueError('public decision requires evidence id and no blocking reasons')
        if self.decision=='BLOCKED' and not self.reasons: raise ValueError('blocked decision requires reasons')

@dataclass(frozen=True,slots=True)
class PublicProjectionRecord:
    projection_id:str; subject_id:str; record_family:str; display_name:str; runtime_mode:str; publication_reference:str; geometry_id:str; geometry_version:int; read_model_version:int=1
    def __post_init__(self):
        if not self.projection_id.startswith('read:nngla:') or not self.publication_reference.startswith('publication:nngla:'): raise ValueError('projection requires governed publication identity')
        if self.runtime_mode not in {'simulation','production'} or not self.geometry_id.startswith('NG-GEO-'): raise ValueError('invalid projection runtime/geometry')
        if self.geometry_version<1 or self.read_model_version<1: raise ValueError('versions must be positive')

@dataclass(frozen=True,slots=True)
class DurablePublicationRecord:
    publication_id:str; subject_id:str; record_family:str; runtime_mode:str; geometry_id:str; geometry_version:int; approved_by:str; submitted_by:str; content_sha256:str
    def __post_init__(self):
        if not self.publication_id.startswith('publication:nngla:') or self.approved_by==self.submitted_by: raise ValueError('publication requires separated governed actors')
        if len(self.content_sha256)!=64: raise ValueError('publication content hash required')

def content_sha256(payload:dict)->str:return sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
