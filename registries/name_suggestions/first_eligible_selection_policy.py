"""Deterministic first-eligible selection policy."""
from __future__ import annotations
from registries.names import CanonicalName
from .suggestion_errors import NameSuggestionCandidateNotFoundError
from .suggestion_selection_policy import SuggestionSelectionPolicy

class FirstEligibleSelectionPolicy(SuggestionSelectionPolicy):
    """Return the first candidate supplied by the repository ordering."""

    def select(self, candidates: tuple[CanonicalName, ...]) -> CanonicalName:
        if not isinstance(candidates, tuple):
            raise TypeError("candidates must be a tuple of CanonicalName records.")
        if any(not isinstance(candidate, CanonicalName) for candidate in candidates):
            raise TypeError("candidates must contain only CanonicalName records.")
        if not candidates:
            raise NameSuggestionCandidateNotFoundError(
                "no eligible canonical name candidate was found."
            )
        return candidates[0]

__all__ = ["FirstEligibleSelectionPolicy"]
