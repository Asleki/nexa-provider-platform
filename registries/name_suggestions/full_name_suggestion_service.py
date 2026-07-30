"""Orchestration service for M009.2.5 full-name suggestions."""
from __future__ import annotations
from registries.names import NameKind, NameRepository
from .full_name_composition import FullNameComposition
from .full_name_suggestion import FullNameSuggestion
from .full_name_suggestion_result import FullNameSuggestionResult
from .pair_name_suggestion import PairNameSuggestion
from .pair_name_suggestion_service import PairNameSuggestionService
from .single_name_suggestion import SingleNameSuggestion
from .single_name_suggestion_service import SingleNameSuggestionService
from .suggestion_selection_policy import SuggestionSelectionPolicy
from .suggestion_support import require_policy,require_repository
from .trio_name_suggestion import TrioNameSuggestion
from .trio_name_suggestion_service import TrioNameSuggestionService

class FullNameSuggestionService:
    def __init__(self, repository: NameRepository, selection_policy: SuggestionSelectionPolicy|None=None)->None:
        repository=require_repository(repository); policy=require_policy(selection_policy)
        self._single=SingleNameSuggestionService(repository,policy)
        self._pair=PairNameSuggestionService(repository,policy)
        self._trio=TrioNameSuggestionService(repository,policy)
    def suggest(self,request:FullNameSuggestion)->FullNameSuggestionResult:
        if not isinstance(request,FullNameSuggestion): raise TypeError("request must be FullNameSuggestion.")
        if request.composition is FullNameComposition.SINGLE_FIRST:
            result=self._single.suggest(SingleNameSuggestion(NameKind.FIRST_NAME,request.runtime_mode))
            return FullNameSuggestionResult(request.composition,result.name)
        if request.composition is FullNameComposition.FIRST_SURNAME:
            result=self._pair.suggest(PairNameSuggestion(request.runtime_mode))
            return FullNameSuggestionResult(request.composition,result.first_name,surname=result.surname)
        result=self._trio.suggest(TrioNameSuggestion(request.runtime_mode))
        return FullNameSuggestionResult(request.composition,result.first_name,result.middle_name,result.surname)

__all__=["FullNameSuggestionService"]
