from __future__ import annotations
import pytest
from shared.events.repositories.event_repository_errors import EventFactoryError,EventNotRegisteredError,EventRepositoryConfigurationError
from shared.events.repositories.event_repository_factory import EventRepositoryFactory
from shared.events.repositories.event_repository_interface import EventRepositoryInterface
from shared.events.repositories.event_repository_registry import EventRepositoryRegistry
from shared.events.repositories.event_repository_types import EventRepositoryType
from shared.events.repositories.memory_event_repository import MemoryEventRepository

class AlternateMemoryEventRepository(MemoryEventRepository): pass
class BrokenRepository(EventRepositoryInterface):
    @property
    def repository_name(self): return "broken"
    @property
    def repository_type(self): return "broken"
    def __init__(self,*a,**k): raise RuntimeError("boom")
    def store(self,e): raise NotImplementedError
    def get(self,e): raise NotImplementedError
    def list_all(self): raise NotImplementedError
    def exists(self,e): raise NotImplementedError
    def count(self): raise NotImplementedError
    def delete(self,e): raise NotImplementedError
    def clear(self): raise NotImplementedError

def test_default_factory_registers_memory():
    f=EventRepositoryFactory(); assert f.registry.is_registered(EventRepositoryType.MEMORY)
def test_factory_accepts_custom_registry():
    r=EventRepositoryRegistry(); f=EventRepositoryFactory(registry=r,register_defaults=False); assert f.registry is r
def test_invalid_registry_rejected():
    with pytest.raises(EventRepositoryConfigurationError): EventRepositoryFactory(registry=object())
def test_register_defaults_idempotent():
    f=EventRepositoryFactory(); c=f.registry.count; f.register_defaults(); assert f.registry.count==c
def test_create_default_memory():
    assert isinstance(EventRepositoryFactory().create(),MemoryEventRepository)
def test_create_by_enum():
    assert isinstance(EventRepositoryFactory().create(EventRepositoryType.MEMORY),MemoryEventRepository)
def test_create_by_string():
    assert isinstance(EventRepositoryFactory().create(" MEMORY "),MemoryEventRepository)
def test_create_passes_kwargs():
    assert EventRepositoryFactory().create(repository_name="abc").repository_name=="abc"
def test_unknown_repo():
    with pytest.raises(EventNotRegisteredError): EventRepositoryFactory(register_defaults=False).create("x")
def test_custom_registry_repo():
    r=EventRepositoryRegistry(); r.register("alt",AlternateMemoryEventRepository); assert isinstance(EventRepositoryFactory(registry=r,register_defaults=False).create("alt"),AlternateMemoryEventRepository)
def test_constructor_failure_wrapped():
    r=EventRepositoryRegistry(); r.register("broken",BrokenRepository)
    with pytest.raises(EventFactoryError) as e: EventRepositoryFactory(registry=r,register_defaults=False).create("broken")
    assert isinstance(e.value.__cause__,RuntimeError)
def test_created_object_must_implement_interface():
    class Fake: pass
    r=EventRepositoryRegistry(); r._repositories["fake"]=Fake
    with pytest.raises(EventFactoryError): EventRepositoryFactory(registry=r,register_defaults=False).create("fake")
def test_multiple_instances():
    f=EventRepositoryFactory(); assert f.create() is not f.create()
def test_registry_unchanged():
    r=EventRepositoryRegistry(); f=EventRepositoryFactory(registry=r,register_defaults=False); assert r.count==0; f.register_defaults(); assert r.count==1
