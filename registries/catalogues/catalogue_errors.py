"""
============================================================
Nexa Provider Platform
File: registries/catalogues/catalogue_errors.py
Layer: Master Registry Foundation
Milestone: NPP-M008.7 — Registry Catalogue
============================================================

Typed, transport-neutral errors raised by Registry Foundation
catalogues. Catalogue errors preserve the common RegistryError
shape without introducing repository, lifecycle, event, audit, or
API responsibilities.
============================================================
"""

from __future__ import annotations

from registries.errors.registry_error import (
    RegistryConflictError,
    RegistryNotFoundError,
    RegistryValidationError,
)


class CatalogueValidationError(RegistryValidationError, ValueError):
    """Raised when catalogue input cannot be safely interpreted."""

    error_code = "NPP-REGISTRY-CATALOGUE-001"

    def __init__(self, message: str, **kwargs: object) -> None:
        kwargs.setdefault("code", self.error_code)
        super().__init__(message, **kwargs)


class CatalogueConflictError(RegistryConflictError, ValueError):
    """Raised when catalogue registration conflicts with an existing entry."""

    error_code = "NPP-REGISTRY-CATALOGUE-010"

    def __init__(self, message: str, **kwargs: object) -> None:
        kwargs.setdefault("code", self.error_code)
        super().__init__(message, **kwargs)


class CatalogueNotFoundError(RegistryNotFoundError, LookupError):
    """Raised when a requested catalogue definition does not exist."""

    error_code = "NPP-REGISTRY-CATALOGUE-020"

    def __init__(self, message: str, **kwargs: object) -> None:
        kwargs.setdefault("code", self.error_code)
        super().__init__(message, **kwargs)


__all__ = [
    "CatalogueConflictError",
    "CatalogueNotFoundError",
    "CatalogueValidationError",
]
