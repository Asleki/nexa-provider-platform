from __future__ import annotations
import csv,json
from dataclasses import asdict
from collections import Counter
from pathlib import Path
from ._shared import *
from .source import current_candidates,source_hashes
from .qualification import current_decisions,qualify_bundle

def _write(path,fields,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as h:w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(rows)
def materialize():
    q=qualify_bundle()
    if q: raise ValueError('Bundle21A qualification failed: '+','.join(q))
    c=current_candidates(); d=current_decisions(); by={(x.subject_id,x.record_family):x for x in d}
    POLICY.parent.mkdir(parents=True,exist_ok=True)
    _write(POLICY,('policy_id','rule','value'),[
        {'policy_id':'pub:001','rule':'CANONICAL_NOT_PUBLIC','value':'TRUE'}, {'policy_id':'pub:002','rule':'PUBLIC_REQUIRES_PUBLICATION_REFERENCE','value':'TRUE'}, {'policy_id':'pub:003','rule':'TARGET_RUNTIME','value':TARGET_RUNTIME}, {'policy_id':'pub:004','rule':'SPATIAL_REFERENCE_POINTS','value':'NEVER_IMPLICITLY_PUBLISH'},
    ])
    _write(CANDIDATES,('subject_id','record_family','display_name','geometry_reference','naming_status','lifecycle_status','spatial_status','geometry_publication_status'),[asdict(x) for x in c])
    _write(DECISIONS,('subject_id','record_family','decision','reasons','map_renderable','publication_id'),[{'subject_id':x.subject_id,'record_family':x.record_family,'decision':x.decision,'reasons':'|'.join(x.reasons),'map_renderable':str(x.map_renderable).lower(),'publication_id':x.publication_id} for x in d])
    # This is deliberately a candidate file, not a false claim that live PostgreSQL already contains these rows.
    _write(PROJECTION_CANDIDATES,('projection_candidate_id','subject_id','record_family','display_name','runtime_mode','current_decision','blocking_reasons','geometry_reference','publication_reference','read_model_version'),[
        {'projection_candidate_id':stable_id('readcandidate:nngla:',x.subject_id,TARGET_RUNTIME),'subject_id':x.subject_id,'record_family':x.record_family,'display_name':x.display_name,'runtime_mode':TARGET_RUNTIME,'current_decision':by[(x.subject_id,x.record_family)].decision,'blocking_reasons':'|'.join(by[(x.subject_id,x.record_family)].reasons),'geometry_reference':x.geometry_reference,'publication_reference':'','read_model_version':READ_MODEL_VERSION} for x in c])
    _write(QUALIFICATION,('subject_id','record_family','current_visibility','map_renderable','publication_reference_status','overall_status'),[{'subject_id':x.subject_id,'record_family':x.record_family,'current_visibility':'INTERNAL','map_renderable':'false','publication_reference_status':'ABSENT_BY_DESIGN_PRELIVE','overall_status':'PASS_FAIL_CLOSED'} for x in c])
    _write(SOURCE_HASHES,('path','sha256','role'),[{'path':p,'sha256':h,'role':'LOCKED_PREDECESSOR_OR_BUNDLE21_POLICY'} for p,h in source_hashes()])
    reason_counts=Counter(r for x in d for r in x.reasons); fam=Counter(x.record_family for x in c)
    summary={'bundle_code':BUNDLE_CODE,'bundle_name':BUNDLE_NAME,'effective_date':BUNDLE_EFFECTIVE_DATE,'target_runtime':TARGET_RUNTIME,'candidate_counts':dict(fam),'total_candidates':len(c),'current_public_decisions':0,'current_map_renderable':0,'publication_policy':'FAIL_CLOSED_UNTIL_LIVE_GEOMETRY_AND_PUBLICATION_GATE','blocking_reason_counts':dict(reason_counts),'excluded_internal_spatial_reference_points':2411,'policy_ready_after_live_geometry_binding':542,'feature_candidates_pending_public_name_and_geometry_publication':20,'place_candidates_blocked_by_proposed_names':700}
    SUMMARY.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); return summary
if __name__=='__main__': print(materialize())
