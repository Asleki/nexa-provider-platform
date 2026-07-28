"""Registry-facing audit integration port for M008.12."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from registries.api.registry_api_request import RegistryApiRequest
    from registries.api.registry_api_response import RegistryApiResponse
    from registries.audit.registry_audit_result import RegistryAuditResult


class RegistryAuditPort(ABC):
    """Contract implemented by registry audit adapters."""

    @abstractmethod
    def record(
        self,
        *,
        request: "RegistryApiRequest",
        response: "RegistryApiResponse",
    ) -> "RegistryAuditResult":
        """Record one registry API outcome and return its audit result."""
        raise NotImplementedError


__all__ = ["RegistryAuditPort"]
