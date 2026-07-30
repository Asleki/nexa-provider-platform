"""Service for M009.2.4 trio suggestions."""
from __future__ import annotations
from registries.names import NameKind, NameRepository
from .suggestion_selection_policy import SuggestionSelectionPolicy
from .suggestion_support import require_policy,require_repository,select_candidate
from .trio_name_suggestion import TrioNameSuggestion
from .trio_name_suggestion_result import TrioNameSuggestionResult

class TrioNameSuggestionService:
    def __init__(self, repository: NameRepository, selection_policy: SuggestionSelectionPolicy | None = None) -> None:
        self._repository=require_repository(repository); self._selection_policy=require_policy(selection_policy)
    def suggest(self, request: TrioNameSuggestion) -> TrioNameSuggestionResult:
        if not isinstance(request,TrioNameSuggestion): raise TypeError("request must be TrioNameSuggestion.")
        return TrioNameSuggestionResult(
            select_candidate(self._repository,self._selection_policy,NameKind.FIRST_NAME,request.runtime_mode),
            select_candidate(self._repository,self._selection_policy,NameKind.MIDDLE_NAME,request.runtime_mode),
            select_candidate(self._repository,self._selection_policy,NameKind.SURNAME,request.runtime_mode),
        )

__all__=["TrioNameSuggestionService"]
