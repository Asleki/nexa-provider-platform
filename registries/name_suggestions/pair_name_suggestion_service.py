"""Service for M009.2.3 first-name and surname suggestions."""
from __future__ import annotations
from registries.names import NameKind, NameRepository
from .pair_name_suggestion import PairNameSuggestion
from .pair_name_suggestion_result import PairNameSuggestionResult
from .suggestion_selection_policy import SuggestionSelectionPolicy
from .suggestion_support import require_policy, require_repository, select_candidate

class PairNameSuggestionService:
    def __init__(self, repository: NameRepository, selection_policy: SuggestionSelectionPolicy | None = None) -> None:
        self._repository=require_repository(repository); self._selection_policy=require_policy(selection_policy)
    def suggest(self, request: PairNameSuggestion) -> PairNameSuggestionResult:
        if not isinstance(request, PairNameSuggestion): raise TypeError("request must be PairNameSuggestion.")
        return PairNameSuggestionResult(
            select_candidate(self._repository,self._selection_policy,NameKind.FIRST_NAME,request.runtime_mode),
            select_candidate(self._repository,self._selection_policy,NameKind.SURNAME,request.runtime_mode),
        )

__all__=["PairNameSuggestionService"]
