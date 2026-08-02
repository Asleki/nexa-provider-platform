from database.migration_control.cli import build_parser
def test_cli_exposes_only_official_commands():
 for cmd in ('status','plan','apply','verify','history'): assert build_parser().parse_args([cmd]).command==cmd


def test_cli_exports_bundle_c_drift_error_and_routes_it_to_drift_exit(monkeypatch,capsys):
 import database.migration_control.cli as cli
 from database.migration_control.errors import MigrationDriftError

 class Connection:
  def close(self): pass
 class Adapter:
  def __init__(self,conn): pass
  def inspect_target(self): return object()
 class Verifier:
  def verify(self,target,actual): raise MigrationDriftError('controlled drift')

 monkeypatch.setattr(cli,'PostgreSQLMigrationAdapter',Adapter)
 monkeypatch.setattr(cli,'MigrationTargetVerifier',Verifier)
 env={'PGHOST':'db.example','PGPORT':'5432','PGUSER':'tester','PGDATABASE':'npp_dev','PGSSLMODE':'require','PGCONNECT_TIMEOUT':'10','NPP_ENVIRONMENT':'development'}
 code=cli.main(['status'],environ=env,password_fn=lambda prompt:'secret',connection_factory_builder=lambda target,password:(lambda:Connection()))
 assert cli.MigrationDriftError is MigrationDriftError
 assert code==cli.EXIT_DRIFT
 assert 'MIGRATION_DATABASE_DRIFT: controlled drift' in capsys.readouterr().err


def test_cli_qualify_routes_report_to_json_not_status(monkeypatch,capsys):
 import json
 import database.migration_control.cli as cli
 from database.migration_control.qualification import QualificationReport
 from database.migration_control.receipts import MigrationOperationReceipt

 class Connection:
  closed=False
  def close(self): self.closed=True
 class Adapter:
  def __init__(self,conn): self.conn=conn
  def inspect_target(self): return object()
 class Actual:
  database_name='npp_dev'
  ssl_enabled=True
 class Verifier:
  def verify(self,target,actual): return Actual()
 class Qualification:
  def __init__(self,service,adapter,drift): pass
  def qualify(self,actual,environment):
   receipt=MigrationOperationReceipt.create(operation='qualify',status='QUALIFIED',database_name='npp_dev',environment_name='development',plan_checksum='a'*64,details=('inspect-target','status'))
   return QualificationReport('npp_dev','development',True,'NOT_BOOTSTRAPPED',4,True,('inspect-target','status'),receipt)

 connection=Connection()
 monkeypatch.setattr(cli,'PostgreSQLMigrationAdapter',Adapter)
 monkeypatch.setattr(cli,'MigrationTargetVerifier',Verifier)
 monkeypatch.setattr(cli,'MigrationQualificationService',Qualification)
 env={'PGHOST':'db.example','PGPORT':'5432','PGUSER':'tester','PGDATABASE':'npp_dev','PGSSLMODE':'require','PGCONNECT_TIMEOUT':'10','NPP_ENVIRONMENT':'development'}
 code=cli.main(['qualify'],environ=env,password_fn=lambda prompt:'secret',connection_factory_builder=lambda target,password:(lambda:connection))
 captured=capsys.readouterr()
 payload=json.loads(captured.out)
 assert code==cli.EXIT_SUCCESS
 assert payload['database_name']=='npp_dev'
 assert payload['ledger_state']=='NOT_BOOTSTRAPPED'
 assert payload['pending_migrations']==4
 assert payload['drift_clean'] is True
 assert payload['receipt']['status']=='QUALIFIED'
 assert captured.err==''
 assert connection.closed is True

def test_cli_qualify_json_mode_is_machine_readable(monkeypatch,capsys):
 import json
 import database.migration_control.cli as cli
 from database.migration_control.qualification import QualificationReport
 from database.migration_control.receipts import MigrationOperationReceipt

 class Connection:
  def close(self): pass
 class Adapter:
  def __init__(self,conn): pass
  def inspect_target(self): return object()
 class Actual:
  database_name='npp_dev'
  ssl_enabled=True
 class Verifier:
  def verify(self,target,actual): return Actual()
 class Qualification:
  def __init__(self,service,adapter,drift): pass
  def qualify(self,actual,environment):
   receipt=MigrationOperationReceipt.create(operation='qualify',status='QUALIFIED',database_name='npp_dev',environment_name='development',details=('history',))
   return QualificationReport('npp_dev','development',True,'NOT_BOOTSTRAPPED',4,True,('history',),receipt)

 monkeypatch.setattr(cli,'PostgreSQLMigrationAdapter',Adapter)
 monkeypatch.setattr(cli,'MigrationTargetVerifier',Verifier)
 monkeypatch.setattr(cli,'MigrationQualificationService',Qualification)
 env={'PGHOST':'db.example','PGPORT':'5432','PGUSER':'tester','PGDATABASE':'npp_dev','PGSSLMODE':'require','PGCONNECT_TIMEOUT':'10','NPP_ENVIRONMENT':'development'}
 code=cli.main(['qualify','--format','json'],environ=env,password_fn=lambda prompt:'secret',connection_factory_builder=lambda target,password:(lambda:Connection()))
 payload=json.loads(capsys.readouterr().out)
 assert code==cli.EXIT_SUCCESS
 assert payload['steps']==['history']
