from threading import RLock
from .contracts import *
class MemoryManualNameCandidateRepository(ManualNameCandidateRepository):
 def __init__(self): self._d={}; self._lock=RLock()
 def add(self,c):
  with self._lock:
   if c.candidate_id in self._d: raise ValueError("candidate already exists.")
   self._d[c.candidate_id]=c; return c
 def get(self,i):
  try:return self._d[i]
  except KeyError: raise KeyError("candidate was not found.")
 def replace(self,c):
  if c.candidate_id not in self._d: raise KeyError("candidate was not found.")
  self._d[c.candidate_id]=c; return c
class MemoryNameAuthorityRepository(NameAuthorityRepository):
 def __init__(self): self._d={}; self._idx={}; self._lock=RLock()
 def create_or_get(self,r):
  with self._lock:
   existing=self._idx.get((r.runtime_mode,r.composition_key))
   if existing:return self._d[existing]
   self._d[r.authority_name_id]=r; self._idx[(r.runtime_mode,r.composition_key)]=r.authority_name_id; return r
 def get(self,i):
  try:return self._d[i]
  except KeyError: raise KeyError("authority name was not found.")
 def find_equivalent(self,runtime_mode,composition_key):
  i=self._idx.get((runtime_mode,composition_key)); return self._d.get(i) if i else None
