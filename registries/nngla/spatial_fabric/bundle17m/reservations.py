
from __future__ import annotations
from threading import Lock
import re
from ._shared import normalize_name_text
from .contracts import NameReservation
from .name_families import family_map,load_family_catalogue
class MemoryNameIdAllocator:
    def __init__(self):
        self._lock=Lock(); self._by_key={}; self._occupied={}; self._next={}
        for code,f in family_map().items():
            ids=[r[f.id_field] for r in load_family_catalogue(code)]; self._occupied[code]=set(ids); nums=[int(x.rsplit('-',1)[1]) for x in ids]; self._next[code]=max(nums,default=0)+1
    def reserve(self,*,family_code,idempotency_key,authority_runtime_mode='production'):
        if authority_runtime_mode!='production': raise ValueError('Simulation may propose names but may not consume sovereign NG-NAM identities')
        f=family_map()[family_code]; key=(family_code,idempotency_key)
        with self._lock:
            if key in self._by_key:return self._by_key[key]
            n=self._next[family_code]
            while f'{f.id_prefix}{n:0{f.sequence_width}d}' in self._occupied[family_code]:n+=1
            if n>999999: raise ValueError('name family namespace exhausted')
            value=f'{f.id_prefix}{n:0{f.sequence_width}d}'; self._next[family_code]=n+1; self._occupied[family_code].add(value); self._by_key[key]=value; return value
class MemoryNameReservationRepository:
    def __init__(self,allocator=None): self.allocator=allocator or MemoryNameIdAllocator(); self._by_scope={}; self._by_idempotency={}
    def reserve(self,*,reservation_id,family_code,display_name,scope_type,scope_reference,idempotency_key):
        key=(family_code,idempotency_key)
        if key in self._by_idempotency:return self._by_idempotency[key]
        match=normalize_name_text(display_name); scope_key=(family_code,match,scope_type,scope_reference)
        if scope_key in self._by_scope: raise ValueError('same-scope name reservation collision')
        nid=self.allocator.reserve(family_code=family_code,idempotency_key=idempotency_key); r=NameReservation(reservation_id,family_code,match,scope_type,scope_reference,nid,idempotency_key,'production','RESERVED'); self._by_scope[scope_key]=r; self._by_idempotency[key]=r; return r
__all__=['MemoryNameIdAllocator','MemoryNameReservationRepository']
