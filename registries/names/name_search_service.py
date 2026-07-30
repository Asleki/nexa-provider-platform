"""Application-neutral search coordinator for the M009.1 catalogue."""
from __future__ import annotations
from .name_repository import NameRepository
from .name_search_query import NameSearchQuery
from .name_search_result import NameSearchResult
class NameSearchService:
    def __init__(self,repository:NameRepository)->None:
        if not isinstance(repository,NameRepository): raise TypeError("repository must implement NameRepository.")
        self._repository=repository
    def search(self,query:NameSearchQuery)->NameSearchResult:
        if not isinstance(query,NameSearchQuery): raise TypeError("query must be NameSearchQuery.")
        return self._repository.search(query)
__all__=["NameSearchService"]
