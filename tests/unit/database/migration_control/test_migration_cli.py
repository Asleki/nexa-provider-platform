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
