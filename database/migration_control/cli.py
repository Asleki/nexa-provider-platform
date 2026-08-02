"""Thin command-line interface for migration control."""
from __future__ import annotations
import argparse,getpass,json,os,sys
from pathlib import Path
from .constants import *
from .connection import MigrationDatabaseTarget,build_psycopg_connection_factory
from .target import MigrationTargetVerifier
from .postgresql import PostgreSQLMigrationAdapter,PostgreSQLMigrationLedger
from .bootstrap import MigrationBootstrapService
from .locking import MigrationLock
from .executor import MigrationExecutor
from .service import MigrationControlService
from .formatting import format_json,format_status
from .errors import *
def build_parser():
    p=argparse.ArgumentParser(prog='python -m database.migration_control'); p.add_argument('command',choices=('status','plan','apply','verify','history')); p.add_argument('--format',choices=tuple(OUTPUT_FORMATS),default='human'); p.add_argument('--yes',action='store_true'); return p
def main(argv=None,*,environ=None,input_fn=input,password_fn=getpass.getpass,connection_factory_builder=build_psycopg_connection_factory):
    args=build_parser().parse_args(argv); env=os.environ if environ is None else environ
    try:
        target=MigrationDatabaseTarget.from_environment(env); password=password_fn(f"Password for user {target.username}: "); factory=connection_factory_builder(target,password)
        conn=factory(); adapter=PostgreSQLMigrationAdapter(conn); actual=MigrationTargetVerifier().verify(target,adapter.inspect_target())
        repo=Path(__file__).resolve().parents[2]; migration_root=repo/'database'/'migrations'; manifest=migration_root/MANIFEST_FILENAME; ledger=PostgreSQLMigrationLedger(adapter)
        bootstrap=MigrationBootstrapService(adapter,Path(__file__).parent/'sql'); service=MigrationControlService(migration_root,manifest,ledger,bootstrap,MigrationLock(adapter),MigrationExecutor(adapter,migration_root))
        if args.command=='status': result=service.status()
        elif args.command=='plan': result=service.plan()
        elif args.command=='verify': result=service.verify()
        elif args.command=='history': result=service.history()
        else:
            if not args.yes and input_fn(f"Type {target.database_name} to confirm: ").strip()!=target.database_name: raise MigrationConfirmationError("migration application was not confirmed.")
            result=service.apply(applied_by=target.username,database_name=actual.database_name,environment_name=target.environment.value,repository_revision=env.get('NPP_REPOSITORY_REVISION','unknown'))
        print(format_json(result) if args.format=='json' else (format_status(result) if hasattr(result,'ledger_state') else format_json(result))); return EXIT_SUCCESS
    except MigrationTargetError as e: print(f"{e.code}: {e.message}",file=sys.stderr); return EXIT_TARGET_MISMATCH
    except MigrationLockError as e: print(f"{e.code}: {e.message}",file=sys.stderr); return EXIT_LOCK_UNAVAILABLE
    except MigrationChecksumError as e: print(f"{e.code}: {e.message}",file=sys.stderr); return EXIT_INTEGRITY_FAILURE
    except MigrationExecutionError as e: print(f"{e.code}: {e.message}",file=sys.stderr); return EXIT_EXECUTION_FAILURE
    except MigrationControlError as e: print(f"{e.code}: {e.message}",file=sys.stderr); return EXIT_OPERATIONAL_FAILURE
    finally:
        try: conn.close()
        except Exception: pass
