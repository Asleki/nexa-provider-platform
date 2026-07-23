"""Nexa Provider Platform — shared audit error contracts (M007.6 revision v4)."""
from __future__ import annotations
from types import MappingProxyType
from typing import Any, Mapping

AUDIT_ERROR_PREFIX = "NPP-AUDIT"

class AuditError(Exception):
    error_code = f"{AUDIT_ERROR_PREFIX}-001"
    def __init__(self, message: str, *, audit_id: str | None = None,
                 action: str | None = None,
                 metadata: Mapping[str, Any] | None = None) -> None:
        if not isinstance(message, str):
            raise TypeError("message must be a string.")
        message = message.strip()
        if not message:
            raise ValueError("message must not be empty.")
        self._message = message
        self._audit_id = self._normalize_optional_text(audit_id, "audit_id")
        self._action = self._normalize_optional_text(action, "action")
        if metadata is not None and not isinstance(metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        self._metadata = MappingProxyType(dict(metadata or {}))
        super().__init__(message)

    @staticmethod
    def _normalize_optional_text(value, field_name):
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")
        value = value.strip()
        if not value:
            raise ValueError(f"{field_name} must not be empty when provided.")
        return value

    @property
    def message(self): return self._message
    @property
    def audit_id(self): return self._audit_id
    @property
    def action(self): return self._action
    @property
    def metadata(self): return self._metadata
    def to_dict(self):
        return {"error_type": self.__class__.__name__, "error_code": self.error_code,
                "message": self.message, "audit_id": self.audit_id,
                "action": self.action, "metadata": dict(self.metadata)}

class AuditValidationError(AuditError, ValueError): error_code=f"{AUDIT_ERROR_PREFIX}-010"
class AuditIdentifierError(AuditValidationError): error_code=f"{AUDIT_ERROR_PREFIX}-011"
class AuditTimestampError(AuditValidationError): error_code=f"{AUDIT_ERROR_PREFIX}-012"
class AuditMetadataError(AuditValidationError): error_code=f"{AUDIT_ERROR_PREFIX}-013"
class AuditRepositoryError(AuditError, RuntimeError): error_code=f"{AUDIT_ERROR_PREFIX}-100"
class AuditRepositoryConfigurationError(AuditRepositoryError, ValueError): error_code=f"{AUDIT_ERROR_PREFIX}-101"
class AuditRepositoryOperationError(AuditRepositoryError): error_code=f"{AUDIT_ERROR_PREFIX}-110"
class AuditAppendError(AuditRepositoryOperationError): error_code=f"{AUDIT_ERROR_PREFIX}-111"
class AuditReadError(AuditRepositoryOperationError): error_code=f"{AUDIT_ERROR_PREFIX}-112"
class AuditListError(AuditRepositoryOperationError): error_code=f"{AUDIT_ERROR_PREFIX}-113"
class AuditExistsError(AuditRepositoryOperationError): error_code=f"{AUDIT_ERROR_PREFIX}-114"
class AuditCountError(AuditRepositoryOperationError): error_code=f"{AUDIT_ERROR_PREFIX}-115"
class AuditRecordRepositoryError(AuditRepositoryError): error_code=f"{AUDIT_ERROR_PREFIX}-120"
class AuditRecordNotFoundError(AuditRecordRepositoryError, LookupError): error_code=f"{AUDIT_ERROR_PREFIX}-121"
class AuditDuplicateRecordError(AuditRecordRepositoryError, ValueError): error_code=f"{AUDIT_ERROR_PREFIX}-122"
class AuditInvalidRecordError(AuditRecordRepositoryError, ValueError): error_code=f"{AUDIT_ERROR_PREFIX}-123"

class AuditQueryError(AuditError, RuntimeError): error_code=f"{AUDIT_ERROR_PREFIX}-200"
class AuditQueryValidationError(AuditQueryError, ValueError): error_code=f"{AUDIT_ERROR_PREFIX}-201"
class AuditQueryServiceConfigurationError(AuditQueryError, ValueError): error_code=f"{AUDIT_ERROR_PREFIX}-202"
class AuditQueryExecutionError(AuditQueryError): error_code=f"{AUDIT_ERROR_PREFIX}-203"
class AuditQueryResultError(AuditQueryError, ValueError): error_code=f"{AUDIT_ERROR_PREFIX}-204"

class AuditIntegrityError(AuditError, RuntimeError): error_code=f"{AUDIT_ERROR_PREFIX}-300"
class AuditIntegrityValidationError(AuditIntegrityError, ValueError): error_code=f"{AUDIT_ERROR_PREFIX}-301"
class AuditIntegrityServiceConfigurationError(AuditIntegrityError, ValueError): error_code=f"{AUDIT_ERROR_PREFIX}-302"
class AuditIntegrityExecutionError(AuditIntegrityError): error_code=f"{AUDIT_ERROR_PREFIX}-303"
class AuditIntegrityResultError(AuditIntegrityError, ValueError): error_code=f"{AUDIT_ERROR_PREFIX}-304"

__all__ = [name for name in globals() if name.startswith("Audit") or name == "AUDIT_ERROR_PREFIX"]
