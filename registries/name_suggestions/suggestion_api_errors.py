"""Typed errors for the M009.2.8 framework-neutral suggestion API."""


class SuggestionApiError(Exception):
    """Base suggestion API error."""


class SuggestionApiValidationError(SuggestionApiError):
    """Raised when a suggestion API request is invalid."""


class SuggestionApiResultError(SuggestionApiError):
    """Raised when a suggestion API response is internally inconsistent."""


class SuggestionApiOperationError(SuggestionApiError):
    """Raised when an operation cannot be executed."""


__all__ = [
    "SuggestionApiError",
    "SuggestionApiOperationError",
    "SuggestionApiResultError",
    "SuggestionApiValidationError",
]
