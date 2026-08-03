"""Repository contracts and in-memory implementation."""
from __future__ import annotations
class ReferenceRepository:
    def add(self,record): raise NotImplementedError
    def get(self,reference_id): raise NotImplementedError
    def find(self,reference_type,runtime_mode,search_label): raise NotImplementedError
    def list_all(self): raise NotImplementedError
class MemoryReferenceRepository(ReferenceRepository):
    def __init__(self): self._items={}
    def add(self,r):
        existing=self.find(r.reference_type.value,r.runtime_mode,r.search_label)
        if existing: return existing
        if r.reference_id in self._items: raise ValueError("reference_id already exists.")
        self._items[r.reference_id]=r; return r
    def get(self,i):
        if i not in self._items: raise KeyError("reference was not found.")
        return self._items[i]
    def find(self,t,rt,s):
        for r in self._items.values():
            if r.reference_type.value==str(t) and r.runtime_mode==rt and r.search_label==s: return r
        return None
    def list_all(self): return tuple(sorted(self._items.values(),key=lambda r:(r.reference_type.value,r.reference_code)))
__all__=["ReferenceRepository","MemoryReferenceRepository"]
