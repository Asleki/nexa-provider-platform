"""Errors for M009.2.2-M009.2.5 core name suggestions."""

class NameSuggestionError(Exception):
    """Base error for automatic name suggestion operations."""

class NameSuggestionCandidateNotFoundError(NameSuggestionError):
    """Raised when no eligible catalogue candidate exists."""

class UnsupportedNameCompositionError(NameSuggestionError):
    """Raised when a requested full-name composition is unsupported."""

__all__ = [
    "NameSuggestionError",
    "NameSuggestionCandidateNotFoundError",
    "UnsupportedNameCompositionError",
]
