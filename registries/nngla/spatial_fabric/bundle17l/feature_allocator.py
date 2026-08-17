
from __future__ import annotations
from threading import Lock
from ._shared import CANONICAL_FEATURES_PATH,csv_rows

def occupied_feature_ids(): return frozenset(r['feature_candidate_id'] for r in csv_rows(CANONICAL_FEATURES_PATH))
class MemoryFeatureIdAllocator:
    def __init__(self,occupied=None):
        self._occupied=set(occupied_feature_ids() if occupied is None else occupied); self._lock=Lock(); self._by_key={}; self._next=max((int(x.rsplit('-',1)[1]) for x in self._occupied),default=0)+1
    def reserve(self,*,candidate_id,idempotency_key,authority_runtime_mode='production'):
        if authority_runtime_mode!='production': raise ValueError('Simulation may form a feature candidate but may not consume sovereign NG-FEAT identities')
        with self._lock:
            if idempotency_key in self._by_key:return self._by_key[idempotency_key]
            while f'NG-FEAT-{self._next:06d}' in self._occupied:self._next+=1
            if self._next>999999: raise ValueError('NG-FEAT six-digit namespace exhausted')
            value=f'NG-FEAT-{self._next:06d}'; self._occupied.add(value); self._next+=1; self._by_key[idempotency_key]=value; return value
__all__=['occupied_feature_ids','MemoryFeatureIdAllocator']
