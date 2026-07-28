"""M008.11 Registry API error hierarchy."""
from __future__ import annotations


class RegistryApiError(Exception):
    """Base error for the transport-neutral Registry API layer."""


class RegistryApiValidationError(RegistryApiError, ValueError):
    """Raised when an API request or operation value is invalid."""


class RegistryApiContractError(RegistryApiError, ValueError):
    """Raised when an API contract declaration is invalid."""


class RegistryApiResultError(RegistryApiError, ValueError):
    """Raised when an API response envelope is internally inconsistent."""


class RegistryApiExecutionError(RegistryApiError):
    """Raised when API orchestration cannot be completed safely."""


__all__ = [
    "RegistryApiContractError",
    "RegistryApiError",
    "RegistryApiExecutionError",
    "RegistryApiResultError",
    "RegistryApiValidationError",
]
