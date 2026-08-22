"""Fail-closed static qualification for the frozen Bundle 19B plan."""
from __future__ import annotations
from ._shared import QUALIFICATION_RESULTS,SOURCE_HASHES,ROOT,EXPECTED_COUNT,csv_rows,sha256_path
from .authoring import load_boundary_candidates
from .geometry import all_coordinates,point_covered
from .source import load_administrative_baseline,load_place_reference_evidence
from .topology import load_topology_policy,load_topology_relationships

def qualification_findings():
    findings=[]; baseline=load_administrative_baseline(); candidates=load_boundary_candidates(); load_topology_policy(); load_topology_relationships()
    byid={x.administrative_area_id:x for x in candidates}; places={r['source_place_code']:(float(r['longitude']),float(r['latitude'])) for r in load_place_reference_evidence()}
    q=csv_rows(QUALIFICATION_RESULTS)
    if len(q)!=EXPECTED_COUNT: findings.append('qualification-count')
    for r in q:
        if r['qualification_status']!='QUALIFIED' or r['geometry_valid']!='true' or r['geometry_nonempty']!='true' or r['sovereign_containment']!='PASS' or r['parent_containment'] not in {'PASS','PASS_SOVEREIGN_PARENT'} or r['sibling_overlap_policy']!='PASS': findings.append('qualification-evidence:'+r['administrative_area_id'])
    for row in baseline:
        c=byid.get(row['administrative_area_id'])
        if c is None: findings.append('missing-boundary:'+row['administrative_area_id']); continue
        if c.administrative_candidate_id!=row['administrative_candidate_id'] or c.source_record_id!=row['source_record_id']: findings.append('identity-drift:'+row['administrative_area_id'])
        for lon,lat in all_coordinates(c.geometry):
            if not (-180<=lon<=180 and -90<=lat<=90): findings.append('coordinate-range:'+row['administrative_area_id']); break
        if row['administrative_type_code']!='REGION':
            p=places.get(row['source_record_id'])
            if p is None or not point_covered(p,c.geometry): findings.append('reference-point-not-covered:'+row['administrative_area_id'])
    for h in csv_rows(SOURCE_HASHES):
        p=ROOT/h['source_path']
        if not p.exists() or sha256_path(p)!=h['sha256']: findings.append('source-hash:'+h['source_path'])
    return tuple(sorted(set(findings)))
def bundle19b_is_qualified(): return qualification_findings()==()
