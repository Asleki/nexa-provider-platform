
from __future__ import annotations
from ._shared import FEATURE_TYPES_PATH,FEATURE_TYPE_EXTENSIONS_PATH,RULES_PATH,csv_rows,bool_text
from .contracts import FeatureQualificationRule

def effective_natural_feature_types():
    rows=csv_rows(FEATURE_TYPES_PATH)+csv_rows(FEATURE_TYPE_EXTENSIONS_PATH)
    seen={};
    for r in rows:
        code=r['feature_type_code']
        if code in seen: raise ValueError(f'feature type redefinition: {code}')
        seen[code]=r
    return {code:r for code,r in seen.items() if r['origin_class']=='NATURAL' and bool_text(r['nngla_recognizable']) and not bool_text(r['nngla_creatable']) and r['status']=='ACTIVE'}

def qualification_rules():
    return tuple(FeatureQualificationRule(
        r['rule_set_id'],r['feature_type_code'],r['engine_domain'],r['geometry_expectation'],bool_text(r['requires_physical_observation']),bool_text(r['requires_geometry']),bool_text(r['requires_spatial_qualification']),bool_text(r['requires_environment_qualification']),bool_text(r['requires_conflict_qualification']),bool_text(r['existing_canonical_reuse_allowed']),bool_text(r['simulation_may_form_candidate']),bool_text(r['production_recognition_required']),bool_text(r['allow_reclassification_same_identity']),bool_text(r['allow_retirement_without_delete']),r['status']) for r in csv_rows(RULES_PATH))

def rule_by_type(): return {r.feature_type_code:r for r in qualification_rules()}
__all__=['effective_natural_feature_types','qualification_rules','rule_by_type']
