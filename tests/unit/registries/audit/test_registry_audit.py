from datetime import datetime, timezone
from itertools import count
import pytest
from registries.adapters.memory import MemoryRegistryRepository
from registries.api import RegistryApi, RegistryApiRequest, RegistryApiResponse
from registries.audit import RegistryAuditContext, RegistryAuditIntegration, RegistryAuditPolicy, RegistryAuditRecordFactory, RegistryAuditResult
from registries.core import BaseRegistry, RegistryDefinition, RegistryFamily
from registries.events import RegistryEventFactory
from shared.audit import AuditAction, AuditOutcome, MemoryAuditRepository
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def item(): return BaseRegistry(RegistryDefinition(registry_id='npp.registry.school',registry_code='SCHOOL',registry_name='School Registry',family=RegistryFamily.SHARED_INFRASTRUCTURE))
def req(op,payload=None,metadata=None): return RegistryApiRequest('req-1',op,NOW,payload or {},metadata or {})
def response(op='get',success=True):
    return RegistryApiResponse.succeeded(request_id='req-1',operation=op,completed_at=NOW,data={}) if success else RegistryApiResponse.failed(request_id='req-1',operation=op,completed_at=NOW,error={'type':'RegistryNotFoundError','message':'missing'})
def test_context_resolves_simulation_and_filters_secrets():
    c=RegistryAuditContext.from_request(req('get',{'registry_id':'x'},{'simulation_agent_id':'l3-1','runtime_mode':'simulation','scenario_id':'s1','card_pin':'1234','nested':{'access_token':'x','ok':1}}))
    assert c.actor_id=='l3-1' and c.actor_type=='simulation_agent' and c.runtime_mode=='simulation'
    assert 'card_pin' not in c.metadata and c.metadata['nested']=={'ok':1}
def test_context_uses_explicit_fallbacks():
    c=RegistryAuditContext.from_request(req('count'))
    assert c.actor_id=='registry-api' and c.actor_type=='system' and c.metadata['actor_resolution']=='fallback'
@pytest.mark.parametrize('operation,action',[('register',AuditAction.REGISTER),('get',AuditAction.READ),('replace',AuditAction.UPDATE),('remove',AuditAction.DELETE),('list',AuditAction.LIST),('exists',AuditAction.READ),('count',AuditAction.READ),('change_status',AuditAction.UPDATE)])
def test_policy_maps_operations(operation,action): assert RegistryAuditPolicy().action_for(operation) is action
def test_policy_maps_outcomes_and_targets():
    p=RegistryAuditPolicy(); assert p.outcome_for(response()) is AuditOutcome.SUCCESS; assert p.outcome_for(response(success=False)) is AuditOutcome.REJECTED
    assert p.target_for(req('count'))==('registry_catalogue','master-registry')
    assert p.target_for(req('register',{'registry':item()}))==('registry','npp.registry.school')
def test_record_factory_links_event_and_governance_metadata():
    ids=count(1); ef=RegistryEventFactory(clock=lambda:NOW,event_id_factory=lambda:f'evt-{next(ids)}')
    api=RegistryApi(MemoryRegistryRepository(),clock=lambda:NOW,event_factory=ef)
    r=req('register',{'registry':item()},{'actor_id':'sup-1','actor_type':'human_supervisor','runtime_id':'run-1','runtime_mode':'simulation','approval_mode':'blind_experiment','decision_intent':'failure_test'})
    response_=api.handle(r)
    record=RegistryAuditRecordFactory(clock=lambda:NOW,audit_id_factory=lambda:'AUD-1').create(r,response_)
    assert record.audit_id=='AUD-1' and record.event_id=='evt-1' and record.event_type=='registry.registered'
    assert record.metadata['approval_mode']=='blind_experiment' and record.metadata['decision_intent']=='failure_test'
def test_record_factory_leaves_reads_unlinked():
    record=RegistryAuditRecordFactory(clock=lambda:NOW,audit_id_factory=lambda:'AUD-1').create(req('count'),response('count'))
    assert record.event_id is None and record.event_type is None
def test_integration_appends_to_shared_repository():
    repo=MemoryAuditRepository(); integration=RegistryAuditIntegration(repo,record_factory=RegistryAuditRecordFactory(clock=lambda:NOW,audit_id_factory=lambda:'AUD-1'))
    result=integration.record(request=req('count'),response=response('count'))
    assert result.success and repo.count().count==1 and result.audit_id=='AUD-1'
def test_result_metadata_reports_attention():
    result=RegistryAuditResult.failed(error_code='X',error_type='Boom',message='failed')
    assert result.to_metadata()['audit_requires_attention'] is True
