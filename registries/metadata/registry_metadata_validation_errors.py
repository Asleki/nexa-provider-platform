"""Structured exceptions for strict registry metadata validation.

These exceptions carry immutable validation results.  They do not mutate,
persist, approve, activate, audit, or otherwise enforce registry metadata.
"""
from __future__ import annotations

from registries.validators.validation_errors import RegistryValidationError
from registries.validators.validation_result import RegistryValidationResult


class InvalidRegistryMetadataError(RegistryValidationError):
    """Raised when strict metadata validation receives an invalid profile."""

    def __init__(self, result: RegistryValidationResult) -> None:
        if not isinstance(result, RegistryValidationResult):
            raise TypeError("result must be a RegistryValidationResult.")
        if result.valid:
            raise ValueError("result must represent invalid validation.")
        self.result = result
        super().__init__(result.summary)


__all__ = ["InvalidRegistryMetadataError"]
