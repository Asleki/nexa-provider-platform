"""Domain errors for M009.2.1 manual catalogue-backed name entry."""


class ManualNameEntryError(Exception):
    """Base error for manual name entry operations."""


class ManualNameComponentNotFoundError(ManualNameEntryError):
    """Raised when a requested atomic component is absent from the catalogue."""


class ManualNameComponentAmbiguousError(ManualNameEntryError):
    """Raised when an exact request resolves to more than one catalogue record."""


__all__ = [
    "ManualNameComponentAmbiguousError",
    "ManualNameComponentNotFoundError",
    "ManualNameEntryError",
]
