"""Thin command-line interface for migration control."""
from __future__ import annotations
import argparse,getpass,os,sys
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
from .drift import MigrationDriftInspector
from .legacy_cleanup import LegacySchemaCleanupService,LEGACY_SCHEMA_ALLOWLIST
from .qualification import MigrationQualificationService
from .errors import (
    MigrationChecksumError,
    MigrationConfirmationError,
    MigrationControlError,
    MigrationDriftError,
    MigrationExecutionError,
    MigrationLockError,
    MigrationTargetError,
)

def build_parser():
    p=argparse.ArgumentParser(prog='python -m database.migration_control')
    p.add_argument('command',choices=('status','plan','apply','verify','history','inspect-target','prepare-development-target','qualify'))
    p.add_argument('--format',choices=tuple(OUTPUT_FORMATS),default='human'); p.add_argument('--yes',action='store_true'); return p

def main(argv=None,*,environ=None,input_fn=input,password_fn=getpass.getpass,connection_factory_builder=build_psycopg_connection_factory):
    args=build_parser().parse_args(argv); env=os.environ if environ is None else environ; conn=None
    try:
        target=MigrationDatabaseTarget.from_environment(env); password=password_fn(f'Password for user {target.username}: '); factory=connection_factory_builder(target,password)
        conn=factory(); adapter=PostgreSQLMigrationAdapter(conn); actual=MigrationTargetVerifier().verify(target,adapter.inspect_target())
        repo=Path(__file__).resolve().parents[2]; migration_root=repo/'database'/'migrations'; manifest=migration_root/MANIFEST_FILENAME; ledger=PostgreSQLMigrationLedger(adapter)
        bootstrap=MigrationBootstrapService(adapter,Path(__file__).parent/'sql'); drift=MigrationDriftInspector(adapter)
        service=MigrationControlService(migration_root,manifest,ledger,bootstrap,MigrationLock(adapter),MigrationExecutor(adapter,migration_root),drift)
        if args.command=='status': result=service.status()
        elif args.command=='plan': result=service.plan()
        elif args.command=='verify': result=service.verify(structural=True)
        elif args.command=='history': result=service.history()
        elif args.command=='inspect-target': result=actual
        elif args.command=='qualify': result=MigrationQualificationService(service,adapter,drift).qualify(actual,target.environment.value)
        elif args.command=='prepare-development-target':
            token=f'CLEAR {target.database_name}'
            confirmed=args.yes or input_fn(f'Type {token} to confirm: ').strip()==token
            result=LegacySchemaCleanupService(adapter,ledger).prepare_development_target(database_name=actual.database_name,environment_name=target.environment.value,schemas=tuple(sorted(LEGACY_SCHEMA_ALLOWLIST)),confirmed=confirmed)
        else:
            expected=target.database_name if target.environment.value!='production' else f'APPLY PRODUCTION {target.database_name}'
            if not args.yes and input_fn(f'Type {expected} to confirm: ').strip()!=expected: raise MigrationConfirmationError('migration application was not confirmed.')
            result=service.apply(applied_by=target.username,database_name=actual.database_name,environment_name=target.environment.value,repository_revision=env.get('NPP_REPOSITORY_REVISION','unknown'))
        print(format_json(result) if args.format=='json' else (format_status(result) if hasattr(result,'ledger_state') else format_json(result))); return EXIT_SUCCESS
    except MigrationTargetError as e: print(f'{e.code}: {e.message}',file=sys.stderr); return EXIT_TARGET_MISMATCH
    except MigrationLockError as e: print(f'{e.code}: {e.message}',file=sys.stderr); return EXIT_LOCK_UNAVAILABLE
    except MigrationChecksumError as e: print(f'{e.code}: {e.message}',file=sys.stderr); return EXIT_INTEGRITY_FAILURE
    except MigrationDriftError as e: print(f'{e.code}: {e.message}',file=sys.stderr); return EXIT_DRIFT
    except MigrationExecutionError as e: print(f'{e.code}: {e.message}',file=sys.stderr); return EXIT_EXECUTION_FAILURE
    except MigrationControlError as e: print(f'{e.code}: {e.message}',file=sys.stderr); return EXIT_OPERATIONAL_FAILURE
    finally:
        if conn is not None:
            try: conn.close()
            except Exception: pass
