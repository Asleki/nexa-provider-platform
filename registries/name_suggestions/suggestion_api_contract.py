"""Framework-neutral suggestion API contract for M009.2.8."""
from __future__ import annotations
from abc import ABC, abstractmethod
from .suggestion_api_request import SuggestionApiRequest
from .suggestion_api_response import SuggestionApiResponse


class SuggestionApiContract(ABC):
    @abstractmethod
    def execute(self, request: SuggestionApiRequest) -> SuggestionApiResponse:
        raise NotImplementedError


__all__ = ["SuggestionApiContract"]
