from datetime import datetime, timezone
from itertools import count

from registries.adapters.memory import MemoryRegistryRepository
from registries.api import RegistryApi, RegistryApiRequest
from registries.audit import RegistryAuditIntegration, RegistryAuditRecordFactory
from registries.core import BaseRegistry, RegistryDefinition, RegistryFamily
from registries.events import RegistryEventFactory
from shared.audit import AuditOutcome, MemoryAuditRepository

NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)


def _registry(*, registry_id="npp.registry.business"):
    return BaseRegistry(
        RegistryDefinition(
            registry_id=registry_id,
            registry_code="BUSINESS",
            registry_name="Business Registry",
            family=RegistryFamily.SHARED_INFRASTRUCTURE,
        )
    )


def _request(request_id, operation, payload=None):
    return RegistryApiRequest(
        request_id,
        operation,
        NOW,
        payload or {},
        {"runtime_mode": "simulation", "correlation_id": "corr-failure-safety"},
    )


def _service():
    events = count(1)
    audits = count(1)
    repository = MemoryRegistryRepository()
    audit_repository = MemoryAuditRepository()
    integration = RegistryAuditIntegration(
        audit_repository,
        record_factory=RegistryAuditRecordFactory(
            clock=lambda: NOW,
            audit_id_factory=lambda: f"AUD-FAIL-{next(audits)}",
        ),
    )
    return (
        RegistryApi(
            repository,
            audit_port=integration,
            clock=lambda: NOW,
            event_factory=RegistryEventFactory(
                clock=lambda: NOW,
                event_id_factory=lambda: f"EVT-FAIL-{next(events)}",
            ),
        ),
        repository,
        audit_repository,
    )


def test_duplicate_registration_is_rejected_without_mutating_existing_state():
    api, repository, audits = _service()
    original = _registry()
    first = api.handle(_request("req-1", "register", {"registry": original}))
    duplicate = api.handle(_request("req-2", "register", {"registry": original}))

    assert first.success
    assert not duplicate.success
    assert duplicate.events == ()
    assert duplicate.error["type"] == "RegistryDuplicateError"
    assert repository.count().count == 1
    assert repository.get(original.registry_id).registry == original
    assert audits.count().count == 2
    rejected_record = audits.list_all().records[-1]
    assert rejected_record.outcome is AuditOutcome.REJECTED
    assert rejected_record.event_id is None


def test_invalid_lifecycle_transition_is_rejected_without_version_change():
    api, repository, audits = _service()
    item = _registry()
    api.handle(_request("req-register", "register", {"registry": item}))
    api.handle(_request("req-active", "change_status", {"registry_id": item.registry_id, "target_status": "active"}))
    api.handle(_request("req-retire", "change_status", {"registry_id": item.registry_id, "target_status": "retired"}))

    before = repository.get(item.registry_id).registry
    rejected = api.handle(
        _request("req-reopen", "change_status", {"registry_id": item.registry_id, "target_status": "active"})
    )
    after = repository.get(item.registry_id).registry

    assert not rejected.success
    assert rejected.events == ()
    assert rejected.error["type"] == "RegistryLifecycleTerminalStateError"
    assert before == after
    assert after.status.value == "retired"
    assert after.version == 3
    assert audits.list_all().records[-1].event_id is None


def test_invalid_registry_definition_never_reaches_repository_or_success_event():
    api, repository, audits = _service()
    invalid = _registry(registry_id="invalid registry id")

    response = api.handle(_request("req-invalid", "register", {"registry": invalid}))

    assert not response.success
    assert response.events == ()
    assert repository.count().count == 0
    assert audits.count().count == 1
    audit = audits.list_all().records[0]
    assert audit.event_id is None
    assert audit.outcome is AuditOutcome.REJECTED
