"""Administrative hierarchy/topology policy contracts."""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
from ._shared import TOPOLOGY_POLICY,TOPOLOGY_RELATIONSHIPS,EXPECTED_TYPE_COUNTS,csv_rows
from .source import load_administrative_baseline
@lru_cache(maxsize=1)
def load_topology_policy():
    rows=csv_rows(TOPOLOGY_POLICY); by={r['administrative_type_code']:r for r in rows}
    if set(by)!=set(EXPECTED_TYPE_COUNTS) or len(rows)!=6: raise ValueError('six administrative topology policies required')
    if by['INDUSTRIAL_ZONE']['partition_mode']!='NON_EXHAUSTIVE_OVERLAY': raise ValueError('industrial zone overlay semantics required')
    if any(r['runtime_effect_scope']!='SHARED_REFERENCE' for r in rows): raise ValueError('policy effect scope mismatch')
    return by
@lru_cache(maxsize=1)
def load_topology_relationships():
    rows=csv_rows(TOPOLOGY_RELATIONSHIPS); baseline=load_administrative_baseline(); ids={r['administrative_area_id'] for r in baseline}
    if len(rows)!=192 or {r['child_administrative_area_id'] for r in rows}!=ids: raise ValueError('every administrative identity requires topology relationship')
    if any(r['topology_status']!='QUALIFIED' for r in rows): raise ValueError('unqualified administrative topology relation')
    return rows
def hierarchy_counts():
    rows=load_administrative_baseline(); return Counter(r['administrative_type_code'] for r in rows)
