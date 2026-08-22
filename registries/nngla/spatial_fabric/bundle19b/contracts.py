"""Immutable P006.7.11.11 administrative-boundary contracts."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re
class GeometryRole(str,Enum): ADMINISTRATIVE_BOUNDARY='ADMINISTRATIVE_BOUNDARY'
class BoundaryOutcome(str,Enum): QUALIFIED='QUALIFIED'; LEGALIZED='LEGALIZED'
@dataclass(frozen=True,slots=True)
class AdministrativeBoundaryCandidate:
    boundary_candidate_id:str; administrative_candidate_id:str; administrative_area_id:str; source_record_id:str
    administrative_type_code:str; canonical_name:str; parent_source_record_id:str; parent_administrative_area_id:str; region_code:str
    geometry_role_code:str; geometry_reservation_key:str; geometry_type_code:str; crs_code:str; authoring_basis:str
    qualification_status:str; legalization_status:str; resulting_boundary_status:str; resulting_lifecycle_status:str; runtime_effect_scope:str
    geometry:dict[str,object]
    def __post_init__(self):
        if not self.boundary_candidate_id.startswith('admbnd:nngla:'): raise ValueError('boundary candidate namespace')
        if not re.fullmatch(r'NG-ADM-\d{6}',self.administrative_area_id): raise ValueError('canonical administrative identity required')
        if self.geometry_role_code!=GeometryRole.ADMINISTRATIVE_BOUNDARY.value: raise ValueError('administrative boundary role required')
        if self.geometry_type_code not in {'POLYGON','MULTIPOLYGON'}: raise ValueError('administrative geometry must be polygonal')
        if self.crs_code!='NG-CRS-EPSG4326': raise ValueError('governed WGS84 CRS required')
        if self.qualification_status!='QUALIFIED': raise ValueError('only qualified boundary candidates are executable')
        if self.runtime_effect_scope!='SHARED_REFERENCE': raise ValueError('administrative geography is shared reference')
@dataclass(frozen=True,slots=True)
class AdministrativeBoundaryExecutionReceipt:
    execution_id:str; fingerprint_sha256:str; database_name:str; environment_name:str; repository_revision:str
    submitter_actor_id:str; approver_actor_id:str; selected_count:int; legalized_count:int; geometry_insert_count:int; status:str; replayed:bool=False
    def __post_init__(self):
        if not self.execution_id.startswith('nnglarun:admin-boundary:'): raise ValueError('execution namespace')
        if not re.fullmatch(r'[0-9a-f]{64}',self.fingerprint_sha256): raise ValueError('fingerprint SHA-256 required')
        if self.submitter_actor_id==self.approver_actor_id: raise ValueError('submitter/approver separation required')
        if self.selected_count!=192 or self.legalized_count!=192 or self.geometry_insert_count!=192: raise ValueError('Bundle 19B exact 192-area contract')
        if (self.status=='REUSED')!=self.replayed: raise ValueError('replay/status mismatch')
