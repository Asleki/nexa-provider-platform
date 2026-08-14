"""P006.7.5/P006.7.6 end-to-end Bundle 15B qualification."""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .bundle15b_source import load_crs_definitions,load_geometry_types,load_survey_accuracy_classes,load_road_classifications,load_geometry_versions,load_survey_control_points,load_road_candidates,load_address_candidates
from .geometry_versions import GeometryAuthorityLevel,GeometryPublicationStatus
from .schema15b_contract import load_schema15b_sql,qualify_schema15b_sql
QUALIFICATION_ID='qualification:novegeo:nngla-bundle15b:v1'
@dataclass(frozen=True,slots=True)
class Bundle15BQualificationReceipt:
    qualification_id:str; status:str; findings:tuple[str,...]
    crs_count:int; geometry_type_count:int; survey_accuracy_class_count:int
    geometry_candidate_count:int; survey_control_candidate_count:int
    road_class_count:int; road_candidate_count:int; address_candidate_count:int

def qualify_bundle15b():
    crs=load_crs_definitions(); gt=load_geometry_types(); acc=load_survey_accuracy_classes(); geos=load_geometry_versions(); controls=load_survey_control_points(); classes=load_road_classifications(); roads=load_road_candidates(); addresses=load_address_candidates(); findings=[]
    if len(crs)!=1: findings.append(f'crs-count:{len(crs)}')
    if len(gt)!=6: findings.append(f'geometry-type-count:{len(gt)}')
    if len(acc)!=6: findings.append(f'survey-accuracy-count:{len(acc)}')
    if len(geos)!=21: findings.append(f'geometry-candidate-count:{len(geos)}')
    if len(controls)!=0: findings.append(f'survey-control-register-must-remain-empty:{len(controls)}')
    if len(classes)!=10: findings.append(f'road-class-count:{len(classes)}')
    if len(roads)!=900: findings.append(f'road-candidate-count:{len(roads)}')
    if len(addresses)!=0: findings.append(f'address-register-must-remain-empty:{len(addresses)}')
    auth=[g for g in geos if g.authoritative_level is GeometryAuthorityLevel.AUTHORITATIVE]
    if len(auth)!=1 or auth[0].subject_id!='country:novegeo' or auth[0].publication_status is not GeometryPublicationStatus.PUBLISHED: findings.append('sovereign-authoritative-geometry-invariant')
    if sum(g.authoritative_level is GeometryAuthorityLevel.QUALIFIED_SOURCE for g in geos)!=20: findings.append('qualified-source-geometry-count')
    if any(r.planning_status!='RESERVED_REFERENCE' for r in roads): findings.append('road-candidates-must-remain-reserved-reference')
    if any(r.geometry_status!='UNMAPPED_PENDING_CONSTRUCTION_OR_SURVEY' or r.geometry_reference is not None for r in roads): findings.append('road-candidates-must-remain-unmapped')
    known={c.road_class_code for c in classes}
    unknown=sorted({r.road_class_code for r in roads}-known)
    if unknown: findings.append('unknown-road-classes:'+','.join(unknown))
    if any(a.horizontal_accuracy_rule!='PENDING_POLICY' or a.vertical_accuracy_rule!='PENDING_POLICY' for a in acc): findings.append('survey-numeric-policy-must-remain-deferred')
    findings.extend(qualify_schema15b_sql(load_schema15b_sql()))
    return Bundle15BQualificationReceipt(QUALIFICATION_ID,'QUALIFIED' if not findings else 'FAILED',tuple(findings),len(crs),len(gt),len(acc),len(geos),len(controls),len(classes),len(roads),len(addresses))
__all__=['QUALIFICATION_ID','Bundle15BQualificationReceipt','qualify_bundle15b']
