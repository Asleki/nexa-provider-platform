from datetime import datetime,timezone
from itertools import count
from registries.adapters.memory import MemoryRegistryRepository
from registries.api import RegistryApi, RegistryApiRequest
from registries.audit import RegistryAuditIntegration, RegistryAuditRecordFactory
from registries.core import BaseRegistry,RegistryDefinition,RegistryFamily
from registries.events import RegistryEventFactory
from registries.ports import RegistryAuditPort
from shared.audit import MemoryAuditRepository
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def item(): return BaseRegistry(RegistryDefinition(registry_id='npp.registry.school',registry_code='SCHOOL',registry_name='School Registry',family=RegistryFamily.SHARED_INFRASTRUCTURE))
def request(op,payload=None): return RegistryApiRequest('req-1',op,NOW,payload or {},{'runtime_mode':'simulation'})
def service(audit_port=None):
    ids=count(1)
    return RegistryApi(MemoryRegistryRepository(),audit_port=audit_port,clock=lambda:NOW,event_factory=RegistryEventFactory(clock=lambda:NOW,event_id_factory=lambda:f'evt-{next(ids)}'))
def test_legacy_api_without_audit_remains_unchanged():
    response=service().handle(request('count'))
    assert response.success and 'audit_success' not in response.metadata
def test_successful_mutation_is_audited_and_event_linked():
    audits=MemoryAuditRepository(); integration=RegistryAuditIntegration(audits,record_factory=RegistryAuditRecordFactory(clock=lambda:NOW,audit_id_factory=lambda:'AUD-1'))
    response=service(integration).handle(request('register',{'registry':item()}))
    assert response.success and response.metadata['audit_success'] and response.metadata['audit_event_id']=='evt-1'
    assert audits.get('AUD-1').record.request_id=='req-1'
def test_failed_registry_operation_is_audited_without_success_event():
    audits=MemoryAuditRepository(); integration=RegistryAuditIntegration(audits,record_factory=RegistryAuditRecordFactory(clock=lambda:NOW,audit_id_factory=lambda:'AUD-1'))
    response=service(integration).handle(request('get',{'registry_id':'missing'}))
    assert not response.success and response.metadata['audit_success'] and audits.get('AUD-1').record.event_id is None
class FailingAuditPort(RegistryAuditPort):
    def record(self,*,request,response): raise RuntimeError('down')
def test_audit_failure_does_not_reverse_completed_registry_mutation():
    api=service(FailingAuditPort()); response=api.handle(request('register',{'registry':item()}))
    assert response.success and api.repository.count().count==1
    assert response.metadata['audit_success'] is False and response.metadata['audit_requires_attention'] is True
