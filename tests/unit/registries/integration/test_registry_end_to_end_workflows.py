from datetime import datetime, timezone
from itertools import count

from registries.adapters.memory import MemoryRegistryRepository
from registries.api import RegistryApi, RegistryApiRequest
from registries.audit import RegistryAuditIntegration, RegistryAuditRecordFactory
from registries.core import BaseRegistry, RegistryDefinition, RegistryFamily
from registries.events import RegistryEventFactory, RegistryEventType
from shared.audit import AuditAction, AuditOutcome, MemoryAuditRepository

NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)


def _registry(registry_id: str = "npp.registry.school", *, version: int = 1) -> BaseRegistry:
    return BaseRegistry(
        RegistryDefinition(
            registry_id=registry_id,
            registry_code="SCHOOL",
            registry_name="School Registry",
            family=RegistryFamily.SHARED_INFRASTRUCTURE,
            version=version,
        )
    )


def _request(request_id: str, operation: str, payload=None) -> RegistryApiRequest:
    return RegistryApiRequest(
        request_id,
        operation,
        NOW,
        payload or {},
        {
            "runtime_id": "nexilabs-novegeo",
            "runtime_mode": "simulation",
            "simulation_agent_id": "nexa-simulation-agent",
            "scenario_id": "novegeo-foundation",
            "correlation_id": "corr-registry-e2e",
            "source": "registry_system_test",
        },
    )


def _service():
    event_ids = count(1)
    audit_ids = count(1)
    registry_repository = MemoryRegistryRepository()
    audit_repository = MemoryAuditRepository()
    audit = RegistryAuditIntegration(
        audit_repository,
        record_factory=RegistryAuditRecordFactory(
            clock=lambda: NOW,
            audit_id_factory=lambda: f"AUD-E2E-{next(audit_ids)}",
        ),
    )
    api = RegistryApi(
        registry_repository,
        audit_port=audit,
        clock=lambda: NOW,
        event_factory=RegistryEventFactory(
            clock=lambda: NOW,
            event_id_factory=lambda: f"EVT-E2E-{next(event_ids)}",
        ),
    )
    return api, registry_repository, audit_repository


def test_complete_registry_workflow_preserves_state_events_and_audit_trace():
    api, repository, audits = _service()
    registry = _registry()

    registered = api.handle(_request("req-register", "register", {"registry": registry}))
    activated = api.handle(
        _request(
            "req-activate",
            "change_status",
            {"registry_id": registry.registry_id, "target_status": "active", "reason": "approved"},
        )
    )
    suspended = api.handle(
        _request(
            "req-suspend",
            "change_status",
            {"registry_id": registry.registry_id, "target_status": "suspended", "reason": "safety review"},
        )
    )
    restored = api.handle(
        _request(
            "req-restore",
            "change_status",
            {"registry_id": registry.registry_id, "target_status": "active", "reason": "review complete"},
        )
    )
    read_back = api.handle(_request("req-get", "get", {"registry_id": registry.registry_id}))
    removed = api.handle(_request("req-remove", "remove", {"registry_id": registry.registry_id}))

    assert all(response.success for response in (registered, activated, suspended, restored, read_back, removed))
    assert registered.events[0].registry_event_type is RegistryEventType.REGISTRY_REGISTERED
    assert activated.events[0].registry_event_type is RegistryEventType.REGISTRY_STATUS_CHANGED
    assert suspended.events[0].payload["current_status"] == "suspended"
    assert restored.events[0].payload["current_status"] == "active"
    assert restored.events[0].payload["registry_version"] == 4
    assert read_back.events == ()
    assert removed.events[0].registry_event_type is RegistryEventType.REGISTRY_REMOVED
    assert repository.count().count == 0

    records = audits.list_all().records
    assert len(records) == 6
    assert [record.request_id for record in records] == [
        "req-register", "req-activate", "req-suspend", "req-restore", "req-get", "req-remove"
    ]
    assert [record.action for record in records] == [
        AuditAction.REGISTER, AuditAction.UPDATE, AuditAction.UPDATE,
        AuditAction.UPDATE, AuditAction.READ, AuditAction.DELETE,
    ]
    assert all(record.outcome is AuditOutcome.SUCCESS for record in records)
    assert records[0].event_id == "EVT-E2E-1"
    assert records[4].event_id is None
    assert records[0].runtime_mode == "simulation"
    assert records[0].runtime_id == "nexilabs-novegeo"
    assert records[0].actor_id == "nexa-simulation-agent"
    assert records[0].metadata["scenario_id"] == "novegeo-foundation"


def test_read_operations_do_not_emit_registry_events_but_are_audited():
    api, _, audits = _service()
    registry = _registry()
    api.handle(_request("req-register", "register", {"registry": registry}))

    responses = (
        api.handle(_request("req-get", "get", {"registry_id": registry.registry_id})),
        api.handle(_request("req-list", "list")),
        api.handle(_request("req-exists", "exists", {"registry_id": registry.registry_id})),
        api.handle(_request("req-count", "count")),
    )

    assert all(response.success and response.events == () for response in responses)
    records = audits.list_all().records
    assert len(records) == 5
    assert all(record.event_id is None for record in records[1:])
    assert [record.action for record in records[1:]] == [
        AuditAction.READ, AuditAction.LIST, AuditAction.READ, AuditAction.READ
    ]
