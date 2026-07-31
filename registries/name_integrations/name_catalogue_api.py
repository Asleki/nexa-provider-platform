"""Transport-neutral Name Catalogue integration API for M009.10.11."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from registries.names.name_search_query import NameSearchQuery
from registries.name_cache import NameCacheRepository
from registries.name_sync import NameSyncRequest,NameCatalogueSnapshot,NameCatalogueChangeSet,NameSyncService

class NameCatalogueApiOperation(str,Enum):
    SEARCH="search"; GET="get"; CACHE_STATE="cache_state"; APPLY_SNAPSHOT="apply_snapshot"; APPLY_CHANGE_SET="apply_change_set"; GET_RECEIPT="get_receipt"

@dataclass(frozen=True,slots=True)
class NameCatalogueView:
    name_id:str; canonical_value:str; search_value:str; name_kind:str; status:str; runtime_mode:str; schema_version:int
    @classmethod
    def from_record(cls,record):
        return cls(record.name_id,record.canonical_value,record.search_value,record.name_kind.value,record.metadata.status.value,record.metadata.runtime_mode,record.metadata.schema_version)

@dataclass(frozen=True,slots=True)
class NameCatalogueApiResponse:
    operation:NameCatalogueApiOperation
    ok:bool
    payload:object=None
    error_code:str|None=None
    message:str=""

class NameCatalogueApi:
    def __init__(self,cache:NameCacheRepository,sync_service:NameSyncService,receipt_repository):
        self._cache=cache; self._sync=sync_service; self._receipts=receipt_repository
    def search(self,query:NameSearchQuery)->NameCatalogueApiResponse:
        if query.runtime_mode is not None and query.runtime_mode!=self._cache.runtime_mode:
            return NameCatalogueApiResponse(NameCatalogueApiOperation.SEARCH,False,error_code="runtime_mismatch",message="query runtime does not match cache runtime")
        result=self._cache.search(query)
        payload={"records":tuple(NameCatalogueView.from_record(r) for r in result.records),"total":result.total,"limit":result.limit,"offset":result.offset}
        return NameCatalogueApiResponse(NameCatalogueApiOperation.SEARCH,True,payload)
    def get(self,name_id:str)->NameCatalogueApiResponse:
        try: entry=self._cache.get(name_id)
        except Exception as exc: return NameCatalogueApiResponse(NameCatalogueApiOperation.GET,False,error_code="not_found",message=str(exc))
        return NameCatalogueApiResponse(NameCatalogueApiOperation.GET,True,NameCatalogueView.from_record(entry.record))
    def cache_state(self)->NameCatalogueApiResponse:
        return NameCatalogueApiResponse(NameCatalogueApiOperation.CACHE_STATE,True,self._cache.get_state())
    def apply_snapshot(self,request:NameSyncRequest,snapshot:NameCatalogueSnapshot)->NameCatalogueApiResponse:
        try: receipt=self._sync.apply_snapshot(request,snapshot)
        except Exception as exc: return NameCatalogueApiResponse(NameCatalogueApiOperation.APPLY_SNAPSHOT,False,error_code="sync_failed",message=str(exc))
        return NameCatalogueApiResponse(NameCatalogueApiOperation.APPLY_SNAPSHOT,receipt.status.value=="completed",receipt)
    def apply_change_set(self,request:NameSyncRequest,changes:NameCatalogueChangeSet)->NameCatalogueApiResponse:
        try: receipt=self._sync.apply_change_set(request,changes)
        except Exception as exc: return NameCatalogueApiResponse(NameCatalogueApiOperation.APPLY_CHANGE_SET,False,error_code="sync_failed",message=str(exc))
        return NameCatalogueApiResponse(NameCatalogueApiOperation.APPLY_CHANGE_SET,receipt.status.value=="completed",receipt)
    def get_receipt(self,request_id:str)->NameCatalogueApiResponse:
        receipt=self._receipts.get_by_request_id(request_id)
        if receipt is None: return NameCatalogueApiResponse(NameCatalogueApiOperation.GET_RECEIPT,False,error_code="not_found",message="receipt not found")
        return NameCatalogueApiResponse(NameCatalogueApiOperation.GET_RECEIPT,True,receipt)
