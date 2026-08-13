from datetime import datetime,timezone
from registries.country.events import CountryEventFactory,CountryEventType
from shared.runtime.operation_runtime import OperationRuntimeMode
def test_country_event_and_audit_share_trace_context():
 t=CountryEventFactory.create(event_type=CountryEventType.COUNTRY_REGISTERED,country_id='country:novegeo',record_version=1,runtime_mode=OperationRuntimeMode.SIMULATION,correlation_id='corr:1',actor_id='actor:1',device_id='device:1',occurred_at=datetime(2026,8,13,tzinfo=timezone.utc))
 assert t.event.payload['runtime_mode']=='simulation'; assert t.audit.event_id==t.event.event_id; assert t.audit.correlation_id=='corr:1'; assert t.audit.runtime_mode=='simulation'
def test_event_runtime_is_explicit_and_production_remains_distinct():
 s=CountryEventFactory.create(event_type=CountryEventType.COUNTRY_QUALIFIED,country_id='country:novegeo',record_version=1,runtime_mode='simulation',correlation_id='c:s',actor_id='a')
 p=CountryEventFactory.create(event_type=CountryEventType.COUNTRY_QUALIFIED,country_id='country:novegeo',record_version=1,runtime_mode='production',correlation_id='c:p',actor_id='a')
 assert s.event.payload['country_id']==p.event.payload['country_id']; assert s.event.runtime_mode is not p.event.runtime_mode
