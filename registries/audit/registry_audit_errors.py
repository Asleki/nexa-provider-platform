"""Registry audit integration errors for M008.12."""
from __future__ import annotations
from types import MappingProxyType
from typing import Any, Mapping

REGISTRY_AUDIT_ERROR_PREFIX = "NPP-REGISTRY-AUDIT"

class RegistryAuditError(Exception):
    error_code = f"{REGISTRY_AUDIT_ERROR_PREFIX}-001"
    def __init__(self, message: str, *, metadata: Mapping[str, Any] | None = None) -> None:
        if not isinstance(message, str): raise TypeError("message must be a string.")
        message = message.strip()
        if not message: raise ValueError("message must not be empty.")
        if metadata is not None and not isinstance(metadata, Mapping): raise TypeError("metadata must be a mapping.")
        self.message = message
        self.metadata = MappingProxyType(dict(metadata or {}))
        super().__init__(message)
    def to_dict(self):
        return {"error_type": type(self).__name__, "error_code": self.error_code, "message": self.message, "metadata": dict(self.metadata)}
class RegistryAuditValidationError(RegistryAuditError, ValueError): error_code=f"{REGISTRY_AUDIT_ERROR_PREFIX}-010"
class RegistryAuditConfigurationError(RegistryAuditError, ValueError): error_code=f"{REGISTRY_AUDIT_ERROR_PREFIX}-020"
class RegistryAuditExecutionError(RegistryAuditError, RuntimeError): error_code=f"{REGISTRY_AUDIT_ERROR_PREFIX}-030"
class RegistryAuditResultError(RegistryAuditError, ValueError): error_code=f"{REGISTRY_AUDIT_ERROR_PREFIX}-040"
__all__=["REGISTRY_AUDIT_ERROR_PREFIX","RegistryAuditError","RegistryAuditValidationError","RegistryAuditConfigurationError","RegistryAuditExecutionError","RegistryAuditResultError"]
