"""Thread-safe deterministic in-memory offline name cache."""
from __future__ import annotations
from threading import RLock
from registries.names.canonical_name import comparison_key
from registries.names.name_search_query import NameSearchQuery
from registries.names.name_search_result import NameSearchResult
from registries.names.name_repository_errors import NameNotFoundError
from .name_cache_models import NameCacheEntry, NameCacheState
from .name_cache_repository import NameCacheRepository
class MemoryNameCacheRepository(NameCacheRepository):
    def __init__(self,runtime_mode:str):
        self._runtime_mode=runtime_mode.strip().lower();
        if not self._runtime_mode: raise ValueError("runtime_mode cannot be empty.")
        self._entries={}; self._state=NameCacheState(self._runtime_mode); self._lock=RLock()
    @property
    def runtime_mode(self): return self._runtime_mode
    def get_state(self):
        with self._lock: return self._state
    def get(self,name_id):
        with self._lock: value=self._entries.get(name_id)
        if value is None: raise NameNotFoundError("cached canonical name was not found.")
        return value
    def _validate(self,entries,state):
        if state.runtime_mode!=self._runtime_mode: raise ValueError("cache state runtime mismatch.")
        ids=set(); identities=set()
        for e in entries:
            if not isinstance(e,NameCacheEntry): raise TypeError("entries must contain NameCacheEntry values.")
            if e.record.metadata.runtime_mode!=self._runtime_mode: raise ValueError("cache entry runtime mismatch.")
            if e.record.name_id in ids or e.record.identity_key in identities: raise ValueError("duplicate cache entry.")
            ids.add(e.record.name_id); identities.add(e.record.identity_key)
    def replace_snapshot(self,entries,state):
        entries=tuple(entries); self._validate(entries,state)
        if state.entry_count!=len(entries): raise ValueError("cache state entry_count mismatch.")
        replacement={e.record.name_id:e for e in entries}
        with self._lock: self._entries=replacement; self._state=state
    def apply_changes(self,upserts,removals,state):
        upserts=tuple(upserts); removals=tuple(removals); self._validate(upserts,state)
        with self._lock:
            replacement=dict(self._entries)
            for rid in removals: replacement.pop(rid,None)
            for e in upserts: replacement[e.record.name_id]=e
            identities={}
            for e in replacement.values():
                other=identities.get(e.record.identity_key)
                if other is not None and other!=e.record.name_id: raise ValueError("identity conflict in cache changes.")
                identities[e.record.identity_key]=e.record.name_id
            if state.entry_count!=len(replacement): raise ValueError("cache state entry_count mismatch.")
            self._entries=replacement; self._state=state
    def search(self,query):
        if not isinstance(query,NameSearchQuery): raise TypeError("query must be NameSearchQuery.")
        if query.runtime_mode is not None and query.runtime_mode!=self._runtime_mode: return NameSearchResult((),0,query.limit,query.offset)
        needle=comparison_key(query.text)
        with self._lock: records=[e.record for e in self._entries.values()]
        records.sort(key=lambda r:(r.metadata.runtime_mode,r.name_kind.value,r.search_value,r.name_id))
        matches=[]
        for r in records:
            if query.name_kind is not None and r.name_kind is not query.name_kind: continue
            if query.status is not None and r.metadata.status is not query.status: continue
            if needle and ((query.exact and r.search_value!=needle) or (not query.exact and not r.search_value.startswith(needle))): continue
            matches.append(r)
        total=len(matches); return NameSearchResult(tuple(matches[query.offset:query.offset+query.limit]),total,query.limit,query.offset)
