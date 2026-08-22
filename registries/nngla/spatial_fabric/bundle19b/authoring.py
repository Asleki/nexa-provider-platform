"""Load and structurally verify the frozen deterministic Bundle 19B boundary-authoring result."""
from __future__ import annotations
from functools import lru_cache
from ._shared import BOUNDARIES,EXPECTED_COUNT,CRS_CODE,EFFECT_SCOPE,json_payload
from .contracts import AdministrativeBoundaryCandidate
@lru_cache(maxsize=1)
def load_boundary_candidates():
    payload=json_payload(BOUNDARIES)
    if payload.get('type')!='FeatureCollection' or len(payload.get('features',()))!=EXPECTED_COUNT: raise ValueError('192 boundary features required')
    if payload.get('metadata',{}).get('crs_code')!=CRS_CODE: raise ValueError('boundary CRS metadata mismatch')
    out=[]
    for f in payload['features']:
        p=f['properties']; g=f['geometry']
        if g.get('type','').upper()!=p['geometry_type_code']: raise ValueError('geometry type/property mismatch')
        out.append(AdministrativeBoundaryCandidate(
          boundary_candidate_id=p['boundary_candidate_id'],administrative_candidate_id=p['administrative_candidate_id'],administrative_area_id=p['administrative_area_id'],
          source_record_id=p['source_record_id'],administrative_type_code=p['administrative_type_code'],canonical_name=p['canonical_name'],
          parent_source_record_id=p['parent_source_record_id'],parent_administrative_area_id=p['parent_administrative_area_id'],region_code=p['region_code'],
          geometry_role_code=p['geometry_role_code'],geometry_reservation_key=p['geometry_reservation_key'],geometry_type_code=p['geometry_type_code'],crs_code=p['crs_code'],
          authoring_basis=p['authoring_basis'],qualification_status=p['qualification_status'],legalization_status=p['legalization_status'],
          resulting_boundary_status=p['resulting_boundary_status'],resulting_lifecycle_status=p['resulting_lifecycle_status'],runtime_effect_scope=p['runtime_effect_scope'],geometry=g))
    if len({x.administrative_area_id for x in out})!=EXPECTED_COUNT or len({x.boundary_candidate_id for x in out})!=EXPECTED_COUNT: raise ValueError('boundary identities must be unique')
    return tuple(sorted(out,key=lambda x:int(x.administrative_area_id.rsplit('-',1)[1])))
