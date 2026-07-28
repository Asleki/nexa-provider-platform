"""Registry-facing audit integration port for M008.12."""
from __future__ import annotations
from abc import ABC,abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from registries.api.registry_api_request import RegistryApiRequest
    from registries.api.registry_api_response import RegistryApiResponse
class RegistryAuditPort(ABC):
    @abstractmethod
    def record(self,*,request:"RegistryApiRequest",response:"RegistryApiResponse"): ...
__all__=["RegistryAuditPort"]
