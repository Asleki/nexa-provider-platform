"""Read-model projection and in-memory cursor search."""
from __future__ import annotations
from dataclasses import replace
import hashlib
from .contracts import *
from registries.names import comparison_key

class NameAuthorityReadModelProjector:
    def project(self,record):
        gen=dict(record.metadata).get("generation",{}) if isinstance(dict(record.metadata).get("generation",{}),dict) else {}
        return NameAuthorityReadModel(record.authority_name_id,record.runtime_mode,record.composition,record.display_name,record.search_name,tuple(x.name_id for x in record.components),tuple(x.canonical_value for x in record.components),record.source_strategy,record.status,gen.get("family"),gen.get("batch_id"),record.schema_version,1,metadata=dict(record.metadata))
    def rebuild(self,records,repository,runtime_mode,read_model_version=1):
        projected=[]
        for r in sorted((x for x in records if x.runtime_mode==runtime_mode),key=lambda x:x.authority_name_id):
            model=replace(self.project(r),read_model_version=read_model_version); repository.upsert(model); projected.append(model)
        raw="\n".join(x.authority_name_id for x in projected); checksum=hashlib.sha256(raw.encode()).hexdigest()
        return ProjectionCheckpoint("name_authority",runtime_mode,projected[-1].authority_name_id if projected else None,len(projected),read_model_version,checksum)

class MemoryNameAuthorityReadRepository:
    def __init__(self): self._d={}
    def upsert(self,m): self._d[m.authority_name_id]=m; return m
    def get(self,i):
        try:return self._d[i]
        except KeyError: raise KeyError("authority read model was not found.")
    def search(self,q):
        cursor=NameAuthoritySearchCursor.decode(q.cursor) if q.cursor else None; text=comparison_key(q.text.strip()) if q.text else ""
        rows=[]
        for x in self._d.values():
            if x.runtime_mode!=q.runtime_mode: continue
            if q.compositions and x.composition not in q.compositions: continue
            if q.generation_families and x.generation_family not in q.generation_families: continue
            if q.statuses and x.status not in q.statuses: continue
            if q.generation_batch_id and x.generation_batch_id!=q.generation_batch_id: continue
            if text and ((x.search_name!=text) if q.exact else (not x.search_name.startswith(text))): continue
            if cursor and (x.search_name,x.authority_name_id)<=(cursor.search_name,cursor.authority_name_id): continue
            rows.append(x)
        rows.sort(key=lambda x:(x.search_name,x.authority_name_id)); page=rows[:q.limit]; more=len(rows)>q.limit
        nxt=NameAuthoritySearchCursor(q.runtime_mode,page[-1].search_name,page[-1].authority_name_id,page[-1].read_model_version).encode() if more and page else None
        return NameAuthoritySearchResult(tuple(page),nxt,more,q.runtime_mode,page[0].read_model_version if page else 1)
    def statistics(self,runtime_mode):
        rows=[x for x in self._d.values() if x.runtime_mode==runtime_mode]; comp={}; fam={}; stat={}
        for x in rows:
            comp[x.composition.value]=comp.get(x.composition.value,0)+1; stat[x.status.value]=stat.get(x.status.value,0)+1
            if x.generation_family: fam[x.generation_family]=fam.get(x.generation_family,0)+1
        return NameAuthorityStatistics(runtime_mode,len(rows),comp,fam,stat)
