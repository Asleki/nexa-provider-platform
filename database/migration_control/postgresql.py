"""DB-API PostgreSQL adapter for migration infrastructure operations."""
from __future__ import annotations
from datetime import datetime
from .target import ActualDatabaseTarget
from .ledger import MigrationLedgerRecord
class PostgreSQLMigrationAdapter:
    def __init__(self,connection): self.connection=connection
    def inspect_target(self):
        with self.connection.cursor() as c:
            c.execute("SELECT current_database(), current_user, session_user, inet_server_addr()::text, inet_server_port(), current_setting('ssl', true), version()")
            r=c.fetchone()
        return ActualDatabaseTarget(r[0],r[1],r[2],r[3],r[4],str(r[5]).lower() in {'on','true','1'},r[6])
    def ledger_exists(self):
        with self.connection.cursor() as c: c.execute("SELECT to_regclass('platform.schema_migration') IS NOT NULL"); return bool(c.fetchone()[0])
    def execute_bootstrap(self,sql):
        with self.connection.cursor() as c: c.execute(sql)
        self.connection.commit()
    def verify_bootstrap(self):
        if not self.ledger_exists(): return False
        with self.connection.cursor() as c:
            c.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='platform' AND table_name='schema_migration'")
            cols={r[0] for r in c.fetchall()}
        return {'migration_id','checksum_sha256','status','sequence_number'}.issubset(cols)
    def try_advisory_lock(self,key):
        with self.connection.cursor() as c: c.execute("SELECT pg_try_advisory_lock(%s)",(key,)); return bool(c.fetchone()[0])
    def release_advisory_lock(self,key):
        try:
            with self.connection.cursor() as c: c.execute("SELECT pg_advisory_unlock(%s)",(key,))
        except Exception: pass
    def execute_migration(self,sql,policy):
        try:
            if policy=='runner_managed':
                with self.connection.transaction():
                    with self.connection.cursor() as c: c.execute(sql)
            else:
                with self.connection.cursor() as c: c.execute(sql)
                if policy=='none': self.connection.commit()
        except Exception:
            try: self.connection.rollback()
            finally: raise
    def ledger_history(self):
        with self.connection.cursor() as c:
            c.execute("SELECT migration_id,milestone_id,filename,sequence_number,checksum_sha256,status,execution_id,started_at,completed_at,execution_duration_ms,applied_by,database_name,environment_name,runner_version,repository_revision,error_code,error_summary FROM platform.schema_migration ORDER BY sequence_number,migration_id")
            return tuple(MigrationLedgerRecord(*r) for r in c.fetchall())
    def ledger_insert_started(self,r):
        with self.connection.cursor() as c: c.execute("INSERT INTO platform.schema_migration (migration_id,milestone_id,filename,sequence_number,checksum_sha256,status,execution_id,started_at,applied_by,database_name,environment_name,runner_version,repository_revision) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(r.migration_id,r.milestone_id,r.filename,r.sequence_number,r.checksum_sha256,r.status,r.execution_id,r.started_at,r.applied_by,r.database_name,r.environment_name,r.runner_version,r.repository_revision))
        self.connection.commit()
    def ledger_update(self,migration_id,status,completed_at,duration_ms,error_code=None,error_summary=None):
        with self.connection.cursor() as c: c.execute("UPDATE platform.schema_migration SET status=%s,completed_at=%s,execution_duration_ms=%s,error_code=%s,error_summary=%s WHERE migration_id=%s AND status='STARTED'",(status,completed_at,duration_ms,error_code,error_summary,migration_id))
        self.connection.commit()
class PostgreSQLMigrationLedger:
    def __init__(self,adapter): self.adapter=adapter
    def is_bootstrapped(self): return self.adapter.ledger_exists()
    def history(self): return self.adapter.ledger_history() if self.is_bootstrapped() else ()
    def get(self,migration_id): return next((r for r in self.history() if r.migration_id==migration_id),None)
    def insert_started(self,record): self.adapter.ledger_insert_started(record)
    def mark_applied(self,migration_id,*,completed_at,duration_ms): self.adapter.ledger_update(migration_id,'APPLIED',completed_at,duration_ms)
    def mark_failed(self,migration_id,*,completed_at,duration_ms,error_code,error_summary): self.adapter.ledger_update(migration_id,'FAILED',completed_at,duration_ms,error_code,error_summary)

# Bundle C inspection and guarded cleanup extensions.
def _inspect_database_objects(self):
    from .drift import DatabaseObjectState
    with self.connection.cursor() as c:
        c.execute("SELECT schema_name FROM information_schema.schemata")
        schemas=frozenset(r[0] for r in c.fetchall())
        c.execute("SELECT table_schema||'.'||table_name FROM information_schema.tables WHERE table_type='BASE TABLE'")
        tables=frozenset(r[0] for r in c.fetchall())
        c.execute("SELECT schemaname||'.'||indexname FROM pg_indexes")
        indexes=frozenset(r[0] for r in c.fetchall())
        c.execute("SELECT tc.table_schema||'.'||tc.constraint_name FROM information_schema.table_constraints tc")
        constraints=frozenset(r[0] for r in c.fetchall())
        c.execute("SELECT table_schema||'.'||table_name FROM information_schema.views")
        views=frozenset(r[0] for r in c.fetchall())
        c.execute("SELECT routine_schema||'.'||routine_name FROM information_schema.routines")
        functions=frozenset(r[0] for r in c.fetchall())
    return DatabaseObjectState(schemas,tables,indexes,constraints,views,functions)

def _inspect_schema_inventory(self,schema_name):
    from .drift import SchemaInventory
    with self.connection.cursor() as c:
        c.execute("""SELECT
          count(*) FILTER (WHERE c.relkind IN ('r','p')),
          count(*) FILTER (WHERE c.relkind='v'),
          count(*) FILTER (WHERE c.relkind='m'),
          count(*) FILTER (WHERE c.relkind='S'),
          count(*) FILTER (WHERE c.relkind='f')
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=%s""",(schema_name,)); rel=c.fetchone()
        c.execute("SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname=%s",(schema_name,)); routines=c.fetchone()[0]
        c.execute("SELECT count(*) FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace WHERE n.nspname=%s AND t.typtype IN ('e','d','c') AND NOT EXISTS (SELECT 1 FROM pg_class c WHERE c.oid=t.typrelid)",(schema_name,)); types=c.fetchone()[0]
    return SchemaInventory(schema_name,rel[0],rel[1],rel[2],rel[3],routines,types,rel[4])

def _drop_empty_schema(self,schema_name):
    if not schema_name.replace('_','').isalnum(): raise ValueError('unsafe schema name')
    with self.connection.cursor() as c: c.execute(f'DROP SCHEMA "{schema_name}"')
    self.connection.commit()

PostgreSQLMigrationAdapter.inspect_database_objects=_inspect_database_objects
PostgreSQLMigrationAdapter.inspect_schema_inventory=_inspect_schema_inventory
PostgreSQLMigrationAdapter.drop_empty_schema=_drop_empty_schema
