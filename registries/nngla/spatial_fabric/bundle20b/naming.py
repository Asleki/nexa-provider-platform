"""Canonical physical-feature geographic-name proposals, preserving existing NG-NAM identities."""
from __future__ import annotations
from .contracts import PhysicalFeatureName
from .source import feature_name_candidates,subject_to_alignment

def physical_feature_names():
    aligned=subject_to_alignment(); out=[]
    family={'RIVER':'RIV','LAKE':'LAK','MOUNTAIN':'MOU','VALLEY':'VAL','PLAIN':'PLN','PLATEAU':'PLT'}
    for r in feature_name_candidates():
        a=aligned[r['source_feature_id']]
        if f"NG-NAM-{family[r['feature_type_code']]}-" not in r['name_id']: raise ValueError('name-family identity mismatch')
        out.append(PhysicalFeatureName(a['canonical_id'],r['source_feature_id'],r['name_id'],r['canonical_name'],r['feature_type_code'],'PROPOSED',r['assignment_candidate_id'],False))
    return tuple(out)
