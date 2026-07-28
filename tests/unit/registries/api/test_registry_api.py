from datetime import datetime, timezone
from itertools import count

from registries.adapters.memory import MemoryRegistryRepository
from registries.api import RegistryApi, RegistryApiRequest
from registries.core import BaseRegistry, RegistryDefinition, RegistryFamily, RegistryStatus
from registries.events import RegistryEventFactory, RegistryEventType

NOW=datetime(2026,7,28,tzinfo=timezone.utc)

def registry(status=RegistryStatus.DRAFT, version=1):
    return BaseRegistry(RegistryDefinition(registry_id="npp.registry.school",registry_code="SCHOOL",registry_name="School Registry",family=RegistryFamily.SHARED_INFRASTRUCTURE,status=status,version=version))

def request(operation,payload=None,metadata=None):
    return RegistryApiRequest("req-1",operation,NOW,payload or {},metadata or {"runtime_mode":"simulation"})

def api():
    ids=count(1)
    return RegistryApi(MemoryRegistryRepository(),clock=lambda:NOW,event_factory=RegistryEventFactory(clock=lambda:NOW,event_id_factory=lambda:f"evt-{next(ids)}"))

def test_register_get_list_exists_count_replace_remove_flow():
    service=api(); item=registry()
    created=service.handle(request("register",{"registry":item}))
    assert created.success and created.events[0].registry_event_type is RegistryEventType.REGISTRY_REGISTERED
    assert service.handle(request("get",{"registry_id":item.registry_id})).success
    assert service.handle(request("exists",{"registry_id":item.registry_id})).success
    assert service.handle(request("count")).success
    assert service.handle(request("list")).success
    replacement=registry(version=2)
    replaced=service.handle(request("replace",{"registry":replacement}))
    assert replaced.success and replaced.events[0].registry_event_type is RegistryEventType.REGISTRY_REPLACED
    removed=service.handle(request("remove",{"registry_id":item.registry_id}))
    assert removed.success and removed.events[0].registry_event_type is RegistryEventType.REGISTRY_REMOVED

def test_change_status_uses_lifecycle_and_emits_event():
    service=api(); item=registry(); service.handle(request("register",{"registry":item}))
    response=service.handle(request("change_status",{"registry_id":item.registry_id,"target_status":"active","reason":"approved"}))
    assert response.success
    assert response.events[0].registry_event_type is RegistryEventType.REGISTRY_STATUS_CHANGED
    assert response.events[0].payload["previous_status"]=="draft"
    assert response.events[0].payload["current_status"]=="active"

def test_failures_are_returned_without_partial_success_events():
    service=api()
    response=service.handle(request("get",{"registry_id":"missing"}))
    assert not response.success and response.events==()
    assert response.error["type"]=="RegistryNotFoundError"

def test_register_validates_definition_before_repository_write():
    service=api()
    invalid=BaseRegistry(RegistryDefinition(registry_id="bad id",registry_code="X",registry_name="Bad",family=RegistryFamily.SHARED_INFRASTRUCTURE))
    response=service.handle(request("register",{"registry":invalid}))
    assert not response.success
    assert service.repository.count().count==0
