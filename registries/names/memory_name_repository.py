"""Thread-safe deterministic in-memory name catalogue repository."""
from __future__ import annotations
from threading import RLock
from .canonical_name import CanonicalName, comparison_key
from .name_repository import NameRepository
from .name_repository_errors import NameAlreadyExistsError,NameIdentityConflictError,NameNotFoundError
from .name_search_query import NameSearchQuery
from .name_search_result import NameSearchResult
class MemoryNameRepository(NameRepository):
    def __init__(self)->None:
        self._records:dict[str,CanonicalName]={}; self._identity_index:dict[tuple[str,str,str],str]={}; self._lock=RLock()
    @staticmethod
    def _record(value:object)->CanonicalName:
        if not isinstance(value,CanonicalName): raise TypeError("record must be CanonicalName.")
        return value
    @staticmethod
    def _id(value:object)->str:
        if not isinstance(value,str): raise TypeError("name_id must be text.")
        value=value.strip()
        if not value: raise ValueError("name_id cannot be empty.")
        return value
    def add(self,record:CanonicalName)->CanonicalName:
        record=self._record(record)
        with self._lock:
            if record.name_id in self._records: raise NameAlreadyExistsError("name_id already exists.")
            existing=self._identity_index.get(record.identity_key)
            if existing is not None: raise NameIdentityConflictError(f"equivalent canonical name already exists as {existing}.")
            self._records[record.name_id]=record; self._identity_index[record.identity_key]=record.name_id
        return record
    def get(self,name_id:str)->CanonicalName:
        ident=self._id(name_id)
        with self._lock: record=self._records.get(ident)
        if record is None: raise NameNotFoundError("canonical name was not found.")
        return record
    def replace(self,record:CanonicalName)->CanonicalName:
        record=self._record(record)
        with self._lock:
            old=self._records.get(record.name_id)
            if old is None: raise NameNotFoundError("canonical name was not found.")
            conflict=self._identity_index.get(record.identity_key)
            if conflict is not None and conflict!=record.name_id: raise NameIdentityConflictError(f"equivalent canonical name already exists as {conflict}.")
            self._identity_index.pop(old.identity_key,None); self._records[record.name_id]=record; self._identity_index[record.identity_key]=record.name_id
        return record
    def exists(self,name_id:str)->bool:
        ident=self._id(name_id)
        with self._lock: return ident in self._records
    def count(self)->int:
        with self._lock: return len(self._records)
    def list_all(self)->tuple[CanonicalName,...]:
        with self._lock: values=tuple(self._records.values())
        return tuple(sorted(values,key=lambda r:(r.metadata.runtime_mode,r.name_kind.value,r.search_value,r.name_id)))
    def search(self,query:NameSearchQuery)->NameSearchResult:
        if not isinstance(query,NameSearchQuery): raise TypeError("query must be NameSearchQuery.")
        needle=comparison_key(query.text)
        matches=[]
        for r in self.list_all():
            if query.name_kind is not None and r.name_kind is not query.name_kind: continue
            if query.status is not None and r.metadata.status is not query.status: continue
            if query.runtime_mode is not None and r.metadata.runtime_mode!=query.runtime_mode: continue
            if needle:
                if query.exact and r.search_value!=needle: continue
                if not query.exact and not r.search_value.startswith(needle): continue
            matches.append(r)
        total=len(matches); page=tuple(matches[query.offset:query.offset+query.limit])
        return NameSearchResult(page,total,query.limit,query.offset)
__all__=["MemoryNameRepository"]
