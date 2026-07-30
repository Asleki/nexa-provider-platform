"""Service for M009.2.2 single-name suggestions."""
from __future__ import annotations
from registries.names import NameRepository
from .single_name_suggestion import SingleNameSuggestion
from .single_name_suggestion_result import SingleNameSuggestionResult
from .suggestion_selection_policy import SuggestionSelectionPolicy
from .suggestion_support import require_policy, require_repository, select_candidate

class SingleNameSuggestionService:
    def __init__(self, repository: NameRepository, selection_policy: SuggestionSelectionPolicy | None = None) -> None:
        self._repository = require_repository(repository)
        self._selection_policy = require_policy(selection_policy)

    def suggest(self, request: SingleNameSuggestion) -> SingleNameSuggestionResult:
        if not isinstance(request, SingleNameSuggestion):
            raise TypeError("request must be SingleNameSuggestion.")
        return SingleNameSuggestionResult(select_candidate(
            self._repository, self._selection_policy, request.name_kind, request.runtime_mode
        ))

__all__ = ["SingleNameSuggestionService"]
