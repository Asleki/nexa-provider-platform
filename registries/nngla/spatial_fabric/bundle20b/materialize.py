from __future__ import annotations
import csv,json
from pathlib import Path
from ._shared import *
from .refinement import hydro_relationships,landform_extents
from .naming import physical_feature_names
from .qualification import qualify_bundle
from .source import source_hashes

def _write(path,fields,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as h:w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(rows)
def materialize():
    q=qualify_bundle()
    if q: raise ValueError('Bundle20B qualification failed: '+','.join(q))
    hydro=hydro_relationships(); ext=landform_extents(); names=physical_feature_names()
    _write(HYDRO_RELATIONSHIPS,('relationship_id','subject_feature_id','subject_physical_id','relationship_type','object_id','evidence_basis','runtime_effect_scope'),[dict(relationship_id=r.relationship_id,subject_feature_id=r.subject_feature_id,subject_physical_id=r.subject_physical_id,relationship_type=r.relationship_type,object_id=r.object_id,evidence_basis=r.evidence_basis,runtime_effect_scope=EFFECT_SCOPE) for r in hydro])
    features=[]
    for e in ext:
        features.append({'type':'Feature','properties':{'feature_id':e.feature_id,'physical_subject_id':e.physical_subject_id,'existing_reference_geometry_id':e.existing_geometry_id,'geometry_role_code':'LANDFORM_EXTENT','geometry_reservation_key':e.geometry_reservation_key,'geometry_id':'','geometry_id_state':'PENDING_GOVERNED_LIVE_RESERVATION','terrain_sample_count':e.terrain_sample_count,'source_basis':e.source_basis,'qualification_status':'QUALIFIED_CANDIDATE','runtime_mode':RUNTIME_MODE,'runtime_effect_scope':EFFECT_SCOPE,'publication_status':'NOT_PUBLISHED'},'geometry':{'type':'Polygon','coordinates':[[[round(x,9),round(y,9)] for x,y in e.polygon]]}})
    LANDFORM_EXTENTS.parent.mkdir(parents=True,exist_ok=True); LANDFORM_EXTENTS.write_text(json.dumps({'type':'FeatureCollection','features':features},indent=2,sort_keys=True)+'\n')
    _write(GEOGRAPHIC_NAMES,('name_id','feature_id','physical_subject_id','canonical_name','name_family','naming_status_code','record_status','runtime_effect_scope','gazette_reference'),[{'name_id':n.name_id,'feature_id':n.feature_id,'physical_subject_id':n.physical_subject_id,'canonical_name':n.canonical_name,'name_family':n.name_family,'naming_status_code':n.naming_status_code,'record_status':'ACTIVE','runtime_effect_scope':EFFECT_SCOPE,'gazette_reference':''} for n in names])
    _write(NAME_ASSIGNMENTS,('assignment_candidate_id','feature_id','physical_subject_id','name_id','canonical_name','assignment_role','assignment_status','official_effect','runtime_effect_scope'),[{'assignment_candidate_id':n.assignment_candidate_id,'feature_id':n.feature_id,'physical_subject_id':n.physical_subject_id,'name_id':n.name_id,'canonical_name':n.canonical_name,'assignment_role':'PRIMARY','assignment_status':'PRESERVED_PROPOSED_UNGAZETTED','official_effect':'false','runtime_effect_scope':EFFECT_SCOPE} for n in names])
    _write(QUALIFICATION,('feature_id','physical_subject_id','name_id','identity_separation','existing_geometry_lineage','name_status','overall_status'),[{'feature_id':n.feature_id,'physical_subject_id':n.physical_subject_id,'name_id':n.name_id,'identity_separation':'PASS','existing_geometry_lineage':'PRESERVED','name_status':'PROPOSED_UNGAZETTED','overall_status':'PASS'} for n in names])
    _write(SOURCE_HASHES,('path','sha256','role'),[{'path':p,'sha256':d,'role':'LOCKED_INPUT_OR_BUNDLE20_OUTPUT'} for p,d in source_hashes()])
    c={'physical_feature_names':len(names),'hydro_relationships':len(hydro),'landform_extent_candidates':len(ext),'existing_hydrology_geometries_preserved':8,'existing_landform_reference_geometries_preserved':12}
    SUMMARY.write_text(json.dumps({'bundle_code':BUNDLE_CODE,'bundle_name':BUNDLE_NAME,'effective_date':BUNDLE_EFFECTIVE_DATE,'counts':c,'naming_effect':'PROPOSED_UNGAZETTED_NO_AUTOMATIC_OFFICIAL_EFFECT','geometry_policy':'PRESERVE_EXISTING_20_FEATURE_GEOMETRY_CHAINS; ADD_EXTENTS_AS_SEPARATE_ROLES'},indent=2,sort_keys=True)+'\n')
    return c
if __name__=='__main__': print(materialize())
