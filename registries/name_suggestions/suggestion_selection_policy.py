"""Selection policy contract for catalogue-backed name suggestions."""
from __future__ import annotations
from abc import ABC, abstractmethod
from registries.names import CanonicalName

class SuggestionSelectionPolicy(ABC):
    """Choose one candidate from an ordered immutable candidate set."""

    @abstractmethod
    def select(self, candidates: tuple[CanonicalName, ...]) -> CanonicalName:
        raise NotImplementedError

__all__ = ["SuggestionSelectionPolicy"]
