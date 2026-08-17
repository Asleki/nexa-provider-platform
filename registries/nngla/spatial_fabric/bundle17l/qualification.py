
from __future__ import annotations
from .contracts import RecognitionDisposition,FeatureRecognitionResult
from .feature_types import rule_by_type,effective_natural_feature_types
from .candidates import recognition_candidates,observation_links
from ._shared import RECOGNITION_RESULTS_PATH,csv_rows,stable_id

def qualify_candidate(candidate,*,has_observation=True,spatial_valid=True,environment_resolved=True,conflict_free=True):
    rules=rule_by_type(); natural=effective_natural_feature_types()
    if candidate.feature_type_code not in natural or candidate.feature_type_code not in rules:
        return FeatureRecognitionResult(stable_id('featresult:nngla:',candidate.candidate_id),candidate.candidate_id,candidate.feature_type_code,RecognitionDisposition.REJECT,'',False,True,False,True,'REJECTED','unsupported-feature-type')
    rule=rules[candidate.feature_type_code]
    geometry_ready=bool(candidate.geometry_reference) and candidate.geometry_status not in {'SOURCE_RESERVED_SECTOR_PENDING_PHYSICAL_GEOMETRY_EXTRACTION','PENDING','UNRESOLVED'}
    qualified=has_observation and spatial_valid and environment_resolved and conflict_free and (geometry_ready or not rule.requires_geometry)
    if candidate.existing_canonical_feature_id and rule.existing_canonical_reuse_allowed:
        return FeatureRecognitionResult(stable_id('featresult:nngla:',candidate.candidate_id),candidate.candidate_id,candidate.feature_type_code,RecognitionDisposition.REUSE_CANONICAL,candidate.existing_canonical_feature_id,True,False,geometry_ready,True,'EXISTING_CANONICAL_REUSED','existing-canonical-identity-preserved')
    if qualified:
        return FeatureRecognitionResult(stable_id('featresult:nngla:',candidate.candidate_id),candidate.candidate_id,candidate.feature_type_code,RecognitionDisposition.RECOGNIZE_NEW,'',True,True,geometry_ready,True,'QUALIFIED_PENDING_PRODUCTION_RECOGNITION','production-recognition-required')
    return FeatureRecognitionResult(stable_id('featresult:nngla:',candidate.candidate_id),candidate.candidate_id,candidate.feature_type_code,RecognitionDisposition.DEFER,'',False,True,geometry_ready,True,'DEFERRED_PENDING_EVIDENCE','geometry-or-qualification-evidence-pending')

def recognition_result_rows(): return csv_rows(RECOGNITION_RESULTS_PATH)
def bundle17l_is_qualified():
    candidates=recognition_candidates(); links=observation_links(); results=recognition_result_rows(); natural=effective_natural_feature_types(); rules=rule_by_type()
    existing=[c for c in candidates if c.existing_canonical_feature_id]
    return len(natural)==22 and len(rules)==22 and len(existing)==21 and len(candidates)==37 and len(links)==49 and len(results)==37 and all(c.feature_type_code in natural for c in candidates) and len({c.candidate_id for c in candidates})==len(candidates)
__all__=['qualify_candidate','recognition_result_rows','bundle17l_is_qualified']
