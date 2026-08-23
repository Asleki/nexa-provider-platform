"""Load physical-feature lineage, hydrology, terrain and the pre-reserved twenty names."""
from __future__ import annotations
from ._shared import *

def physical_feature_alignment():
    rows=[r for r in csv_rows(CANONICAL_ALIGNMENT) if r['object_family']=='GEOGRAPHIC_FEATURE' and r['canonical_id']!='NG-FEAT-000001']
    if len(rows)!=20: raise ValueError('expected 20 non-mainland physical feature alignments')
    return tuple(rows)

def subject_to_alignment(): return {r['source_record_id']:r for r in physical_feature_alignment()}
def feature_name_candidates():
    rows=csv_rows(FEATURE_NAMES)
    if len(rows)!=20 or any(r['assignment_status']!='PROPOSED_UNGAZETTED' for r in rows): raise ValueError('expected exactly 20 governed ungazetted physical-feature name proposals')
    return rows

def source_hashes(): return tuple((str(p.relative_to(ROOT)),sha256_path(p)) for p in INPUT_PATHS if p.exists())
