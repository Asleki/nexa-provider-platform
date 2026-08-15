"""Terminal interface for governed NNGLA previews, execution, verification and history."""
from __future__ import annotations
import argparse, getpass, json, os, subprocess
from dataclasses import asdict
from database.migration_control.connection import MigrationDatabaseTarget, build_psycopg_connection_factory
from .execution import ExecutionRequest, ExecutionService, confirmation_token
from .selectors import Selector
from .persistence import PostgreSQLExecutionRepository
from .verification import verify_receipt

def _revision():
    try:return subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    except Exception:return "UNRESOLVED"

def _repo():
    target=MigrationDatabaseTarget.from_environment(os.environ)
    password=getpass.getpass(f"Password for user {target.username}: ")
    conn=build_psycopg_connection_factory(target,password)()
    return conn,PostgreSQLExecutionRepository(conn,database_name=target.database_name,environment_name=target.environment.value)

def _selector(args): return Selector(after_id=args.after_id,limit=args.limit) if args.after_id or args.limit else None

def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    for name in ("preview","execute"):
        q=sub.add_parser(name); q.add_argument("--plan",required=True); q.add_argument("--limit",type=int); q.add_argument("--after-id")
    e=sub.choices["execute"]; e.add_argument("--fingerprint",required=True); e.add_argument("--submitter",required=True); e.add_argument("--approver",required=True)
    sub.add_parser("history")
    args=p.parse_args(argv); conn,repo=_repo()
    try:
        service=ExecutionService(repo)
        if args.cmd=="history":
            print(json.dumps([list(row) for row in repo.history()],indent=2,default=str)); return 0
        preview=service.preview_for_execution(args.plan,selector_override=_selector(args),repository_revision=_revision())
        token=confirmation_token(args.plan,preview.database_name,preview.fingerprint)
        if args.cmd=="preview":
            print(json.dumps({"plan_id":preview.plan_id,"selected_count":preview.selected_count,"qualification_counts":dict(preview.qualification_counts),"schema_ready":preview.schema_ready,"execution_ready":preview.execution_ready,"fingerprint":preview.fingerprint,"confirmation_token":token,"database_writes":0},indent=2)); return 0
        confirmation=input(f"Type exact confirmation token:\n{token}\n> ")
        receipt=service.run(ExecutionRequest(args.plan,_revision(),args.submitter,args.approver,args.fingerprint,confirmation,_selector(args)))
        report=verify_receipt(receipt)
        print(json.dumps({"receipt":asdict(receipt),"verification":asdict(report)},indent=2,default=str)); return 0 if report.passed else 2
    finally: conn.close()

if __name__=="__main__": raise SystemExit(main())
