
from __future__ import annotations
from ._shared import RECOGNITION_CANDIDATES_PATH,OBSERVATION_LINKS_PATH,csv_rows,stable_id
from .contracts import FeatureCandidate,ObservationLink

def recognition_candidates():
    return tuple(FeatureCandidate(r['candidate_id'],r['source_feature_id'],r['feature_type_code'],r['source_dataset_id'],r['source_record_reference'],r['physical_origin_class'],r['geometry_reference'],r['geometry_status'],r['qualification_status'],r['existing_canonical_feature_id'],r['runtime_mode'],r['runtime_effect_scope'],r['candidate_status']) for r in csv_rows(RECOGNITION_CANDIDATES_PATH))
def observation_links():
    return tuple(ObservationLink(r['link_id'],r['candidate_id'],r['observation_type'],r['source_dataset_id'],r['source_record_id'],r['source_path_reference'],r['source_sha256'],r['evidence_status']) for r in csv_rows(OBSERVATION_LINKS_PATH))
def form_candidate(*,source_feature_id,feature_type_code,source_dataset_id,source_record_reference,geometry_reference='',geometry_status='UNRESOLVED',qualification_status='PENDING',runtime_mode='simulation',runtime_effect_scope='SIMULATION_ONLY',existing_canonical_feature_id=''):
    cid=stable_id('featcand:nngla:',source_dataset_id,source_feature_id,feature_type_code)
    return FeatureCandidate(cid,source_feature_id,feature_type_code,source_dataset_id,source_record_reference,'NATURAL',geometry_reference,geometry_status,qualification_status,existing_canonical_feature_id,runtime_mode,runtime_effect_scope,'CANDIDATE')
__all__=['recognition_candidates','observation_links','form_candidate']
