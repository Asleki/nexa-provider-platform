from datetime import datetime, timezone

from registries.adapters.memory import MemoryRegistryRepository
from registries.api import RegistryApi, RegistryApiRequest, RegistryApiResponse
from registries.core import BaseRegistry, RegistryDefinition, RegistryFamily
from registries.events import RegistryEventFactory

NOW = datetime(2026, 7, 28, 12, 0, tzinfo=timezone.utc)


def _registry(registry_id, code):
    return BaseRegistry(
        RegistryDefinition(
            registry_id=registry_id,
            registry_code=code,
            registry_name=f"{code.title()} Registry",
            family=RegistryFamily.SHARED_INFRASTRUCTURE,
        )
    )


def _request(request_id, operation, payload=None):
    return RegistryApiRequest(request_id, operation, NOW, payload or {}, {"runtime_mode": "simulation"})


def _api():
    return RegistryApi(
        MemoryRegistryRepository(),
        clock=lambda: NOW,
        event_factory=RegistryEventFactory(clock=lambda: NOW, event_id_factory=lambda: "EVT-DETERMINISTIC"),
    )


def test_registry_api_response_and_event_round_trips_are_deterministic():
    api = _api()
    response = api.handle(
        _request("req-register", "register", {"registry": _registry("npp.registry.school", "SCHOOL")})
    )

    first = response.to_dict()
    second = response.to_dict()
    event_payload = response.events[0].to_dict()

    assert first == second
    assert response.events[0].to_dict() == event_payload
    assert RegistryApiResponse(
        request_id=response.request_id,
        operation=response.operation,
        completed_at=response.completed_at,
        success=response.success,
        data=response.data,
        events=response.events,
        metadata=response.metadata,
    ).to_dict() == first


def test_repository_listing_preserves_deterministic_insertion_order():
    api = _api()
    registries = (
        _registry("npp.registry.country", "COUNTRY"),
        _registry("npp.registry.school", "SCHOOL"),
        _registry("npp.registry.bank", "BANK"),
    )
    for index, registry in enumerate(registries, start=1):
        assert api.handle(_request(f"req-{index}", "register", {"registry": registry})).success

    first = api.repository.list_all().to_dict()
    second = api.repository.list_all().to_dict()

    assert first == second
    assert [item.registry_id for item in api.repository.list_all().registries] == [
        registry.registry_id for registry in registries
    ]


def test_request_payload_and_metadata_are_snapshot_immutable():
    payload = {"registry_id": "npp.registry.school"}
    metadata = {"runtime_mode": "simulation"}
    request = RegistryApiRequest("req-snapshot", "get", NOW, payload, metadata)

    payload["registry_id"] = "changed"
    metadata["runtime_mode"] = "production"

    assert request.payload["registry_id"] == "npp.registry.school"
    assert request.metadata["runtime_mode"] == "simulation"
