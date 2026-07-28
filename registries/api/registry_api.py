"""Transport-neutral orchestration façade for M008.11 Registry APIs."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any

from registries.core import BaseRegistry, RegistryDefinition
from registries.events import RegistryEventFactory
from registries.governance import RegistryLifecycle
from registries.ports import RegistryAuditPort, RegistryRepositoryInterface
from registries.validators import RegistryValidator
from shared.events import EventMetadata

from .registry_api_contract import RegistryApiContract
from .registry_api_errors import RegistryApiExecutionError
from .registry_api_operation import RegistryApiOperation
from .registry_api_request import RegistryApiRequest
from .registry_api_response import RegistryApiResponse

Clock = Callable[[], datetime]


class RegistryApi:
    """Coordinate registry operations without transport or persistence coupling."""

    def __init__(
        self,
        repository: RegistryRepositoryInterface,
        *,
        lifecycle: RegistryLifecycle | None = None,
        event_factory: RegistryEventFactory | None = None,
        contract: RegistryApiContract | None = None,
        audit_port: RegistryAuditPort | None = None,
        clock: Clock | None = None,
    ) -> None:
        if not isinstance(repository, RegistryRepositoryInterface):
            raise TypeError("repository must implement RegistryRepositoryInterface.")
        self._repository = repository
        self._lifecycle = lifecycle or RegistryLifecycle()
        self._event_factory = event_factory or RegistryEventFactory()
        self._contract = contract or RegistryApiContract()
        if audit_port is not None and not isinstance(audit_port, RegistryAuditPort):
            raise TypeError("audit_port must implement RegistryAuditPort.")
        self._audit_port = audit_port
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @property
    def repository(self) -> RegistryRepositoryInterface:
        return self._repository

    @property
    def contract(self) -> RegistryApiContract:
        return self._contract

    def handle(self, request: RegistryApiRequest) -> RegistryApiResponse:
        """Return a stable success/failure envelope for one API request."""
        if not isinstance(request, RegistryApiRequest):
            raise TypeError("request must be a RegistryApiRequest.")
        completed_at = self._now()
        if not self.contract.supports(request.operation):
            response = self._failure(request, completed_at, RegistryApiExecutionError(
                f"Operation {request.operation.value!r} is not enabled by the contract."
            ))
            return self._with_audit(request, response)
        try:
            data, events = self._execute(request)
            response = RegistryApiResponse.succeeded(
                request_id=request.request_id,
                operation=request.operation,
                completed_at=completed_at,
                data=data,
                events=events,
                metadata={"api": self.contract.name, "api_version": self.contract.version},
            )
        except Exception as exc:
            response = self._failure(request, completed_at, exc)
        return self._with_audit(request, response)

    def execute(self, request: RegistryApiRequest) -> RegistryApiResponse:
        """Alias for handle, suitable for application-service callers."""
        return self.handle(request)

    def _execute(self, request: RegistryApiRequest):
        operation = request.operation
        if operation is RegistryApiOperation.REGISTER:
            registry = self._registry_from_payload(request.payload)
            RegistryValidator.validate_or_raise(registry)
            result = self.repository.add(registry)
            event = self._event_factory.registered(
                registry, metadata=self._event_metadata(request)
            )
            return {"repository_result": result.to_dict()}, (event,)
        if operation is RegistryApiOperation.GET:
            result = self.repository.get(self._registry_id(request.payload))
            return {"repository_result": result.to_dict()}, ()
        if operation is RegistryApiOperation.REPLACE:
            registry = self._registry_from_payload(request.payload)
            RegistryValidator.validate_or_raise(registry)
            result = self.repository.replace(registry)
            event = self._event_factory.replaced(
                registry, metadata=self._event_metadata(request)
            )
            return {"repository_result": result.to_dict()}, (event,)
        if operation is RegistryApiOperation.REMOVE:
            registry_id = self._registry_id(request.payload)
            existing = self.repository.get(registry_id).registry
            if existing is None:
                raise RegistryApiExecutionError("repository returned no registry to remove.")
            result = self.repository.remove(registry_id)
            event = self._event_factory.removed(
                existing, metadata=self._event_metadata(request)
            )
            return {"repository_result": result.to_dict()}, (event,)
        if operation is RegistryApiOperation.LIST:
            result = self.repository.list_all()
            return {"repository_result": result.to_dict()}, ()
        if operation is RegistryApiOperation.EXISTS:
            result = self.repository.exists(self._registry_id(request.payload))
            return {"repository_result": result.to_dict()}, ()
        if operation is RegistryApiOperation.COUNT:
            result = self.repository.count()
            return {"repository_result": result.to_dict()}, ()
        if operation is RegistryApiOperation.CHANGE_STATUS:
            registry_id = self._registry_id(request.payload)
            target_status = request.payload.get("target_status")
            if target_status is None:
                raise RegistryApiExecutionError("payload.target_status is required.")
            current = self.repository.get(registry_id).registry
            if current is None:
                raise RegistryApiExecutionError("repository returned no registry.")
            transition = self._lifecycle.transition(current, target_status)
            if not transition.changed:
                raise RegistryApiExecutionError("status transition produced no state change.")
            result = self.repository.replace(transition.registry)
            event = self._event_factory.status_changed(
                transition,
                metadata=self._event_metadata(request),
                reason=request.payload.get("reason"),
            )
            return {"repository_result": result.to_dict(), "lifecycle": transition.to_dict()}, (event,)
        raise RegistryApiExecutionError(f"Unsupported operation: {operation.value}.")

    @staticmethod
    def _registry_from_payload(payload: Mapping[str, Any]) -> BaseRegistry:
        value = payload.get("registry")
        if isinstance(value, BaseRegistry):
            return value
        if isinstance(value, RegistryDefinition):
            return BaseRegistry.from_definition(value)
        if isinstance(value, Mapping):
            return BaseRegistry.from_dict(value)
        raise RegistryApiExecutionError(
            "payload.registry must be BaseRegistry, RegistryDefinition, or mapping."
        )

    @staticmethod
    def _registry_id(payload: Mapping[str, Any]) -> str:
        value = payload.get("registry_id")
        if not isinstance(value, str) or not value.strip():
            raise RegistryApiExecutionError("payload.registry_id must be non-empty text.")
        return value.strip()

    @staticmethod
    def _event_metadata(request: RegistryApiRequest) -> EventMetadata:
        metadata = request.metadata
        return EventMetadata(
            correlation_id=str(metadata.get("correlation_id") or request.request_id),
            causation_id=metadata.get("causation_id"),
            actor_id=metadata.get("actor_id"),
            device_id=metadata.get("device_id"),
            source=str(metadata.get("source") or "registry_api"),
            attributes={
                key: value for key, value in metadata.items()
                if key not in {"correlation_id", "causation_id", "actor_id", "device_id", "source"}
            },
        )

    def _with_audit(self, request: RegistryApiRequest, response: RegistryApiResponse) -> RegistryApiResponse:
        if self._audit_port is None:
            return response
        try:
            result = self._audit_port.record(request=request, response=response)
            audit_metadata = result.to_metadata()
        except Exception as exc:
            audit_metadata = {
                "audit_attempted": True,
                "audit_success": False,
                "audit_error_code": getattr(exc, "error_code", "NPP-REGISTRY-AUDIT-030"),
                "audit_error_type": type(exc).__name__,
                "audit_requires_attention": True,
            }
        metadata = dict(response.metadata)
        metadata.update(audit_metadata)
        if response.success:
            return RegistryApiResponse.succeeded(
                request_id=response.request_id, operation=response.operation,
                completed_at=response.completed_at, data=response.data,
                events=response.events, metadata=metadata,
            )
        return RegistryApiResponse.failed(
            request_id=response.request_id, operation=response.operation,
            completed_at=response.completed_at, error=response.error, metadata=metadata,
        )

    def _failure(self, request, completed_at, exc):
        return RegistryApiResponse.failed(
            request_id=request.request_id,
            operation=request.operation,
            completed_at=completed_at,
            error={
                "type": type(exc).__name__,
                "message": str(exc),
                "module": type(exc).__module__,
            },
            metadata={"api": self.contract.name, "api_version": self.contract.version},
        )

    def _now(self) -> datetime:
        value = self._clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise RegistryApiExecutionError("clock must return timezone-aware datetime.")
        return value.astimezone(timezone.utc)


__all__ = ["Clock", "RegistryApi"]
