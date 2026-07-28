"""Mapping policy between Registry API operations and shared audit contracts."""
from __future__ import annotations
from registries.api import RegistryApiOperation, RegistryApiRequest, RegistryApiResponse
from registries.core import BaseRegistry, RegistryDefinition
from shared.audit import AuditAction, AuditOutcome
from .registry_audit_errors import RegistryAuditValidationError

_ACTIONS={RegistryApiOperation.REGISTER:AuditAction.REGISTER,RegistryApiOperation.GET:AuditAction.READ,RegistryApiOperation.REPLACE:AuditAction.UPDATE,RegistryApiOperation.REMOVE:AuditAction.DELETE,RegistryApiOperation.LIST:AuditAction.LIST,RegistryApiOperation.EXISTS:AuditAction.READ,RegistryApiOperation.COUNT:AuditAction.READ,RegistryApiOperation.CHANGE_STATUS:AuditAction.UPDATE}
class RegistryAuditPolicy:
    def action_for(self,operation):
        try:return _ACTIONS[RegistryApiOperation.parse(operation)]
        except Exception as exc: raise RegistryAuditValidationError("unsupported registry audit operation.") from exc
    def outcome_for(self,response):
        if not isinstance(response,RegistryApiResponse): raise RegistryAuditValidationError("response must be RegistryApiResponse.")
        if response.success:return AuditOutcome.SUCCESS
        error_type=str((response.error or {}).get("type", ""))
        return AuditOutcome.FAILURE if error_type in {"RuntimeError","RegistryStorageError","RegistryApiExecutionError"} else AuditOutcome.REJECTED
    def target_for(self,request):
        if not isinstance(request,RegistryApiRequest): raise RegistryAuditValidationError("request must be RegistryApiRequest.")
        if request.operation in {RegistryApiOperation.LIST,RegistryApiOperation.COUNT}: return ("registry_catalogue","master-registry")
        value=request.payload.get("registry_id")
        registry=request.payload.get("registry")
        if value is None and isinstance(registry,(BaseRegistry,RegistryDefinition)): value=registry.registry_id
        elif value is None and isinstance(registry,dict): value=registry.get("registry_id")
        return ("registry", value.strip() if isinstance(value,str) and value.strip() else "unresolved")
__all__=["RegistryAuditPolicy"]
