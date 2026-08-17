from __future__ import annotations
from threading import Lock
from registries.nngla.spatial_fabric.bundle17j import occupied_geometry_ids
class MemoryGeometryIdAllocator:
 def __init__(self,occupied=None):
  self._occupied=set(occupied_geometry_ids() if occupied is None else occupied); self._next=max((int(x.rsplit('-',1)[1]) for x in self._occupied),default=0)+1; self._lock=Lock(); self._by_key={}
 def reserve(self,*,idempotency_key:str,authority_runtime_mode='production'):
  if authority_runtime_mode!='production': raise ValueError('Simulation may propose geometry change but may not consume sovereign geometry IDs')
  with self._lock:
   if idempotency_key in self._by_key:return self._by_key[idempotency_key]
   while f'NG-GEO-{self._next:06d}' in self._occupied:self._next+=1
   if self._next>999999: raise ValueError('NG-GEO six-digit namespace exhausted')
   gid=f'NG-GEO-{self._next:06d}'; self._next+=1; self._occupied.add(gid); self._by_key[idempotency_key]=gid; return gid
__all__=['MemoryGeometryIdAllocator']
