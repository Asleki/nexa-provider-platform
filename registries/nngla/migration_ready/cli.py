"""Terminal interface for NNGLA Migration Ready and record-atomic Phase 17.1.0MR."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import getpass
import json
import os
import subprocess

from database.migration_control.connection import (
    MigrationDatabaseTarget,
    build_psycopg_connection_factory,
)
from registries.nngla.spatial_fabric.bundle17e.persistence import PostgreSQLSpatialRepository

from .candidate_state import assess_candidate_state
from .catalogue import ROOT, load_batch_profiles, load_domain_plan
from .empty_registers import assess_empty_registers
from .locking import postgresql_migration_lock
from .orchestrator import (
    PLAN_ID,
    build_spatial_preview,
    confirmation_token,
    execute_spatial,
)
from .preflight import inspect_preflight
from .record_execution import (
    RecordExecutionInterrupted,
    build_record_preview,
    execute_records,
    record_confirmation_token,
)
from .record_persistence import RecordAtomicPersistence
from .verification import verify_migration_ready


def _revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "UNRESOLVED"


def _connect():
    target = MigrationDatabaseTarget.from_environment(os.environ)
    password = getpass.getpass(f"Password for user {target.username}: ")
    connection = build_psycopg_connection_factory(target, password)()
    return target, connection


def _json(value) -> None:
    print(json.dumps(value, indent=2, default=str, sort_keys=True))


def _batch_args(parser: argparse.ArgumentParser) -> None:
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--profile", default="initial-spatial-2411")
    modes.add_argument("--batch-size", type=int)


def _record_window_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--count", type=int, required=True, help="Logical record-window size, not transaction size")
    parser.add_argument(
        "--start-ordinal",
        type=int,
        help="Explicit governed NG-SPT ordinal for duplicate/range verification; omit for next/resume",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NNGLA Migration Ready operational CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inventory", help="Inspect locked source/domain and batch-profile policy without database writes")
    sub.add_parser("preflight", help="Read-only live PostgreSQL readiness inspection")

    preview_parser = sub.add_parser("preview-spatial", help="Read-only legacy 2,411-point batch migration preview")
    _batch_args(preview_parser)
    execute_parser = sub.add_parser("execute-spatial", help="Execute predecessor transactional spatial batches")
    _batch_args(execute_parser)
    execute_parser.add_argument("--fingerprint", required=True)
    execute_parser.add_argument("--submitter", required=True)
    execute_parser.add_argument("--approver", required=True)

    record_preview = sub.add_parser(
        "preview-records",
        help="Preview deterministic record-atomic next/resume or explicit verification window",
    )
    _record_window_args(record_preview)
    record_execute = sub.add_parser(
        "execute-records",
        help="Execute one logical NNGLA window with one durable transaction/receipt per new coordinate",
    )
    _record_window_args(record_execute)
    record_execute.add_argument("--fingerprint", required=True)
    record_execute.add_argument("--submitter", required=True)
    record_execute.add_argument("--approver", required=True)
    record_history = sub.add_parser("record-history", help="Show per-coordinate migration/import history")
    record_history.add_argument("--start-ordinal", type=int)
    record_history.add_argument("--count", type=int)

    sub.add_parser("verify", help="Verify migrated spatial truth, baseline immutability and empty-register readiness")
    sub.add_parser("history", help="Show Migration Ready / Bundle 17E spatial execution receipts")
    return parser


def _preview_payload(preview) -> dict:
    action_by_id = {item.coordinate_candidate_id: item.action.value for item in preview.reconciliation}
    batches = []
    for window in preview.batches:
        actions = [action_by_id[candidate_id] for candidate_id in window.candidate_ids]
        batches.append(
            {
                "batch_number": window.batch_number,
                "selected_count": window.selected_count,
                "insert_count": actions.count("INSERT_NEW"),
                "reuse_count": actions.count("REUSE_CANONICAL"),
                "conflict_count": actions.count("CONFLICT"),
                "first_candidate_id": window.candidate_ids[0],
                "last_candidate_id": window.candidate_ids[-1],
            }
        )
    return {
        "database_name": preview.database_name,
        "environment_name": preview.environment_name,
        "profile_id": preview.profile_id,
        "total_count": preview.total_count,
        "insert_count": preview.insert_count,
        "reuse_count": preview.reuse_count,
        "conflict_count": preview.conflict_count,
        "execution_ready": preview.execution_ready,
        "source_sha256": preview.source_sha256,
        "repository_revision": preview.repository_revision,
        "fingerprint": preview.fingerprint,
        "confirmation_token": confirmation_token(preview.database_name, preview.fingerprint),
        "database_writes": 0,
        "batches": batches,
    }


def _record_preview_payload(preview) -> dict:
    window = None if preview.window is None else asdict(preview.window)
    logical_batch_id = None if preview.window is None else preview.window.logical_batch_id
    return {
        "database_name": preview.database_name,
        "environment_name": preview.environment_name,
        "plan_version": 3,
        "source_order": "CANONICAL_NG_SPT_ORDINAL",
        "requested_count": preview.requested_count,
        "progress": asdict(preview.progress),
        "window": window,
        "selected_count": preview.selected_count,
        "insert_count": preview.insert_count,
        "reuse_count": preview.reuse_count,
        "conflict_count": preview.conflict_count,
        "migration_complete": preview.migration_complete,
        "execution_ready": preview.execution_ready,
        "source_sha256": preview.source_sha256,
        "repository_revision": preview.repository_revision,
        "fingerprint": preview.fingerprint,
        "confirmation_token": record_confirmation_token(
            preview.database_name, logical_batch_id, preview.fingerprint
        ),
        "database_writes": 0,
    }


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "inventory":
        candidate = assess_candidate_state(ROOT)
        empty = assess_empty_registers(ROOT)
        _json(
            {
                "domain_plan": [asdict(item) for item in load_domain_plan()],
                "batch_profiles": {key: asdict(value) for key, value in load_batch_profiles().items()},
                "candidate_state": asdict(candidate),
                "empty_registers": [asdict(item) for item in empty],
                "database_writes": 0,
            }
        )
        return 0 if candidate.passed and all(item.ready for item in empty) else 2

    target, connection = _connect()
    try:
        repository = PostgreSQLSpatialRepository(connection)
        if args.command == "history":
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT execution_id,plan_id,status,selected_count,inserted_count,reused_count,"
                    "started_at,completed_at FROM geography.nngla_execution_receipt "
                    "WHERE plan_id IN (%s,%s) ORDER BY completed_at,execution_id",
                    ("P006.7.11.7.7-8-BUNDLE17E", PLAN_ID),
                )
                rows = [
                    {
                        "execution_id": str(row[0]),
                        "plan_id": str(row[1]),
                        "status": str(row[2]),
                        "selected_count": int(row[3]),
                        "inserted_count": int(row[4]),
                        "reused_count": int(row[5]),
                        "started_at": row[6],
                        "completed_at": row[7],
                    }
                    for row in cur.fetchall()
                ]
            _json(rows)
            return 0

        if args.command == "record-history":
            if args.count is not None and args.count < 1:
                parser.error("--count must be positive")
            rows = RecordAtomicPersistence(repository).record_history(
                plan_id=PLAN_ID,
                database_name=target.database_name,
                environment_name=target.environment.value,
                start_ordinal=args.start_ordinal,
                count=args.count,
            )
            _json({"database_name": target.database_name, "records": rows, "database_writes": 0})
            return 0

        preflight = inspect_preflight(ROOT, connection, target.environment.value)
        if args.command == "preflight":
            _json({**asdict(preflight), "ready": preflight.ready, "database_writes": 0})
            return 0 if preflight.ready else 2
        if not preflight.ready:
            _json({"error": "PREFLIGHT_FAILED", "preflight": {**asdict(preflight), "ready": False}})
            return 2

        if args.command == "preview-spatial":
            preview = build_spatial_preview(
                repository,
                database_name=target.database_name,
                environment_name=target.environment.value,
                repository_revision=_revision(),
                profile_id=args.profile,
                batch_size=args.batch_size,
            )
            _json(_preview_payload(preview))
            return 0 if preview.execution_ready else 2

        if args.command == "execute-spatial":
            with postgresql_migration_lock(connection):
                preview = build_spatial_preview(
                    repository,
                    database_name=target.database_name,
                    environment_name=target.environment.value,
                    repository_revision=_revision(),
                    profile_id=args.profile,
                    batch_size=args.batch_size,
                )
                token = confirmation_token(target.database_name, preview.fingerprint)
                print("Type exact confirmation token:")
                print(token)
                confirmation = input("> ")
                results = execute_spatial(
                    repository,
                    database_name=target.database_name,
                    environment_name=target.environment.value,
                    repository_revision=_revision(),
                    approved_fingerprint=args.fingerprint,
                    confirmation=confirmation,
                    submitter_actor_id=args.submitter,
                    approver_actor_id=args.approver,
                    profile_id=args.profile,
                    batch_size=args.batch_size,
                )
            _json(
                {
                    "status": "COMPLETE",
                    "database_name": target.database_name,
                    "profile_id": preview.profile_id,
                    "batches": [asdict(item) for item in results],
                    "inserted_count": sum(item.inserted_count for item in results),
                    "reused_count": sum(item.reused_count for item in results),
                }
            )
            return 0

        if args.command == "preview-records":
            preview = build_record_preview(
                repository,
                database_name=target.database_name,
                environment_name=target.environment.value,
                repository_revision=_revision(),
                requested_count=args.count,
                start_ordinal=args.start_ordinal,
            )
            _json(_record_preview_payload(preview))
            return 0 if preview.execution_ready else 2

        if args.command == "execute-records":
            with postgresql_migration_lock(connection):
                preview = build_record_preview(
                    repository,
                    database_name=target.database_name,
                    environment_name=target.environment.value,
                    repository_revision=_revision(),
                    requested_count=args.count,
                    start_ordinal=args.start_ordinal,
                )
                logical_batch_id = None if preview.window is None else preview.window.logical_batch_id
                token = record_confirmation_token(target.database_name, logical_batch_id, preview.fingerprint)
                print("Type exact confirmation token:")
                print(token)
                confirmation = input("> ")
                try:
                    result = execute_records(
                        repository,
                        database_name=target.database_name,
                        environment_name=target.environment.value,
                        repository_revision=_revision(),
                        requested_count=args.count,
                        start_ordinal=args.start_ordinal,
                        approved_fingerprint=args.fingerprint,
                        confirmation=confirmation,
                        submitter_actor_id=args.submitter,
                        approver_actor_id=args.approver,
                    )
                except RecordExecutionInterrupted as exc:
                    _json(
                        {
                            "status": "INTERRUPTED",
                            "failed_ordinal": exc.failed_ordinal,
                            "inserted_count_observed_this_process": exc.inserted_count,
                            "reused_count_observed_this_process": exc.reused_count,
                            "last_committed_ordinal_observed_this_process": exc.last_committed_ordinal,
                            "message": str(exc),
                            "resume_rule": "Reconnect and run preview-records again; PostgreSQL is authoritative.",
                        }
                    )
                    return 3
            _json({"database_name": target.database_name, **asdict(result)})
            return 0

        if args.command == "verify":
            report = verify_migration_ready(
                ROOT,
                connection,
                database_name=target.database_name,
                environment_name=target.environment.value,
            )
            _json({**asdict(report), "passed": report.passed})
            return 0 if report.passed else 2

        parser.error(f"unsupported command: {args.command}")
        return 2
    finally:
        try:
            connection.close()
        except Exception:
            pass


__all__ = ["build_parser", "main"]
