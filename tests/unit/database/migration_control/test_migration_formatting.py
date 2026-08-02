from database.migration_control.service import MigrationStatus
from database.migration_control.formatting import format_status,format_json
def test_formats_are_stable_and_machine_readable():
 s=MigrationStatus('NOT_BOOTSTRAPPED',4,0,4,0,0,0,0,'a'*64); assert 'Pending migrations: 4' in format_status(s); assert 'ledger_state' in format_json(s)


def test_format_json_serializes_immutable_migration_plan_metadata():
 from json import loads
 from database.migration_control.contracts import ExpectedObjects,MigrationArtifact,MigrationDefinition,MigrationIdentity,MigrationPlan
 identity=MigrationIdentity(1,'m009_10_04_name_catalogue','M009.10.4','Name catalogue')
 forward=MigrationArtifact('m009_10_04_name_catalogue.sql','forward','a'*64,1,'embedded')
 rollback=MigrationArtifact('m009_10_04_name_catalogue_rollback.sql','rollback','b'*64,1,'embedded')
 definition=MigrationDefinition(identity,forward,rollback,(),ExpectedObjects(schemas=('reference',)),metadata={'source':'repository','tags':('name','catalogue')})
 plan=MigrationPlan((definition,),(definition,),'c'*64,'d'*64)
 rendered=loads(format_json(plan))
 assert rendered['forward_order'][0]['metadata']=={'source':'repository','tags':['name','catalogue']}
 assert dict(definition.metadata)=={'source':'repository','tags':('name','catalogue')}


def test_format_json_handles_nested_immutable_collections_deterministically():
 from json import loads
 from types import MappingProxyType
 value=MappingProxyType({'roles':frozenset({'verify','plan'}),'nested':MappingProxyType({'enabled':True})})
 first=format_json(value); second=format_json(value)
 assert first==second
 assert loads(first)=={'nested':{'enabled':True},'roles':['plan','verify']}


def test_format_json_serializes_qualification_report_and_receipt():
 from json import loads
 from database.migration_control.qualification import QualificationReport
 from database.migration_control.receipts import MigrationOperationReceipt
 receipt=MigrationOperationReceipt.create(operation='qualify',status='QUALIFIED',database_name='npp_dev',environment_name='development',plan_checksum='a'*64,details=('inspect-target','status','plan'))
 report=QualificationReport('npp_dev','development',True,'NOT_BOOTSTRAPPED',4,True,('inspect-target','status','plan'),receipt)
 rendered=loads(format_json(report))
 assert rendered['database_name']=='npp_dev'
 assert rendered['environment_name']=='development'
 assert rendered['tls_enabled'] is True
 assert rendered['ledger_state']=='NOT_BOOTSTRAPPED'
 assert rendered['pending_migrations']==4
 assert rendered['drift_clean'] is True
 assert rendered['steps']==['inspect-target','status','plan']
 assert rendered['receipt']['operation']=='qualify'
 assert rendered['receipt']['status']=='QUALIFIED'
