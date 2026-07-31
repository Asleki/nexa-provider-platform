"""Storage-neutral offline name cache contract."""
from __future__ import annotations
from abc import ABC, abstractmethod
from registries.names.name_search_query import NameSearchQuery
from registries.names.name_search_result import NameSearchResult
from .name_cache_models import NameCacheEntry, NameCacheState
class NameCacheRepository(ABC):
    @property
    @abstractmethod
    def runtime_mode(self)->str: ...
    @abstractmethod
    def get_state(self)->NameCacheState: ...
    @abstractmethod
    def get(self,name_id:str)->NameCacheEntry: ...
    @abstractmethod
    def search(self,query:NameSearchQuery)->NameSearchResult: ...
    @abstractmethod
    def replace_snapshot(self,entries:tuple[NameCacheEntry,...],state:NameCacheState)->None: ...
    @abstractmethod
    def apply_changes(self,upserts:tuple[NameCacheEntry,...],removals:tuple[str,...],state:NameCacheState)->None: ...
