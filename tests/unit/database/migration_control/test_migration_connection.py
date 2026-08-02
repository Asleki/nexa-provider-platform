from database.migration_control.connection import MigrationDatabaseTarget

def test_environment_target_never_stores_password():
 t=MigrationDatabaseTarget.from_environment({'PGHOST':'h','PGDATABASE':'d','PGUSER':'u','PGPASSWORD':'secret'})
 assert 'secret' not in repr(t)
