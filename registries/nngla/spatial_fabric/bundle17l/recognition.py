
from __future__ import annotations
from dataclasses import replace
from .feature_allocator import MemoryFeatureIdAllocator
from .qualification import qualify_candidate
from .contracts import RecognitionDisposition

def recognize_candidate(candidate,*,allocator=None,idempotency_key,authority_runtime_mode='production',**qualification_inputs):
    result=qualify_candidate(candidate,**qualification_inputs)
    if result.disposition is RecognitionDisposition.REUSE_CANONICAL:return result
    if result.disposition is not RecognitionDisposition.RECOGNIZE_NEW:return result
    if authority_runtime_mode!='production': raise ValueError('Production authority required to recognize new canonical physical feature')
    allocator=allocator or MemoryFeatureIdAllocator(); fid=allocator.reserve(candidate_id=candidate.candidate_id,idempotency_key=idempotency_key,authority_runtime_mode=authority_runtime_mode)
    return replace(result,canonical_feature_id=fid,result_status='RECOGNIZED',findings='new-canonical-feature-identity-reserved')
__all__=['recognize_candidate']
