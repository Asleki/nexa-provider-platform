"""Locked administrative/source reconciliation for Bundle 19B."""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
from ._shared import ADMIN_SOURCE,CANONICAL_ALIGNMENT,BOUNDARY_REQUESTS,PLACE_POINTS,EXPECTED_COUNT,EXPECTED_TYPE_COUNTS,EFFECT_SCOPE,csv_rows
@lru_cache(maxsize=1)
def load_administrative_baseline():
    admins=csv_rows(ADMIN_SOURCE); align={r['candidate_id']:r for r in csv_rows(CANONICAL_ALIGNMENT) if r['object_family']=='ADMINISTRATIVE_AREA'}
    requests={r['administrative_candidate_id']:r for r in csv_rows(BOUNDARY_REQUESTS)}
    if len(admins)!=EXPECTED_COUNT or len(align)!=EXPECTED_COUNT or len(requests)!=EXPECTED_COUNT: raise ValueError('exactly 192 administrative baseline rows required')
    out=[]
    for ordinal,row in enumerate(admins,1):
        a=align.get(row['administrative_candidate_id']); q=requests.get(row['administrative_candidate_id'])
        if not a or not q: raise ValueError('administrative alignment/request missing')
        expected=f'NG-ADM-{ordinal:06d}'
        if a['canonical_id']!=expected: raise ValueError('locked NG-ADM suffix allocation changed')
        if row['boundary_status']!='BOUNDARY_PENDING_LEGALIZATION' or row['lifecycle_status_code']!='PROVISIONAL' or row['geometry_reference']:
            raise ValueError('Bundle 19B requires untouched provisional no-geometry administrative source')
        if q['candidate_status']!='PENDING_BOUNDARY_AUTHORING' or q['current_geometry_reference'] or q['candidate_geometry_reference']:
            raise ValueError('boundary request is not pristine')
        merged=dict(row); merged['administrative_area_id']=expected; out.append(merged)
    if Counter(r['administrative_type_code'] for r in out)!=Counter(EXPECTED_TYPE_COUNTS): raise ValueError('administrative type counts changed')
    by_source={r['source_record_id']:r for r in out}
    for r in out:
        if r['administrative_type_code']=='REGION':
            if r['parent_source_record_id']!='country:novegeo': raise ValueError('region parent must be sovereign country')
        elif r['parent_source_record_id'] not in by_source: raise ValueError('administrative parent missing')
        if r['runtime_effect_scope']!=EFFECT_SCOPE: raise ValueError('runtime effect scope changed')
    return tuple(out)
@lru_cache(maxsize=1)
def load_place_reference_evidence():
    rows=csv_rows(PLACE_POINTS)
    if len(rows)!=700 or any(r['outcome_status'] not in {'QUALIFIED','QUALIFIED_WITH_EXCEPTION'} for r in rows): raise ValueError('completed Bundle 19A place geography required')
    return rows
