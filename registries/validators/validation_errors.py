"""
============================================================
Nexa Provider Platform
File: registries/validators/validation_errors.py
Layer: Master Registry Foundation
Milestone: NPP-M008.9 — Registry Validation
============================================================

Validation-specific exceptions for registry definition enforcement.
The exceptions carry immutable structured validation results and do
not persist, publish, audit, or mutate registry state.
============================================================
"""

from __future__ import annotations

from .validation_result import RegistryValidationResult


class RegistryValidationError(ValueError):
    """Base error for Registry Validation Foundation failures."""


class InvalidRegistryDefinitionError(RegistryValidationError):
    """Raised when strict validation receives an invalid definition."""

    def __init__(self, result: RegistryValidationResult) -> None:
        if not isinstance(result, RegistryValidationResult):
            raise TypeError("result must be a RegistryValidationResult.")
        if result.valid:
            raise ValueError("result must represent invalid validation.")
        self.result = result
        super().__init__(result.summary)


__all__ = (
    "InvalidRegistryDefinitionError",
    "RegistryValidationError",
)
