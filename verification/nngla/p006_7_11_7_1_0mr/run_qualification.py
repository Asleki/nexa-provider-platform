#!/usr/bin/env python3
"""Read-only qualification for Bundle 17.1.0MR record-atomic NNGLA migration."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys

_DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_DEFAULT_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_DEFAULT_REPO_ROOT))

from database.migration_control.connection import (
    MigrationDatabaseTarget,
    build_psycopg_connection_factory,
)
from registries.nngla.migration_ready.preflight import inspect_preflight
from registries.nngla.migration_ready.record_execution import (
    PLAN_ID,
    PLAN_VERSION,
    build_record_preview,
)
from registries.nngla.migration_ready.record_persistence import RecordAtomicPersistence
from registries.nngla.spatial_fabric.bundle17e.persistence import PostgreSQLSpatialRepository

EXPECTED_PLAN_ID = "P006.7.11.7.0MR-SPATIAL-BATCH"
EXPECTED_PLAN_VERSION = 3


def _revision(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "UNRESOLVED"


def _static(root: Path) -> dict:
    findings: list[str] = []
    required = (
        "record_contracts.py",
        "record_progress.py",
        "record_persistence.py",
        "record_execution.py",
    )
    package = root / "registries/nngla/migration_ready"
    for filename in required:
        if not (package / filename).is_file():
            findings.append(f"RECORD_MODULE_MISSING:{filename}")

    record_execution = (package / "record_execution.py").read_text(encoding="utf-8")
    record_progress = (package / "record_progress.py").read_text(encoding="utf-8")
    cli = (package / "cli.py").read_text(encoding="utf-8")
    manifest = json.loads((root / "database/migrations/migration_manifest.json").read_text(encoding="utf-8"))
    predecessor = root / "verification/nngla/p006_7_11_7_1mr/run_qualification.py"

    if PLAN_ID != EXPECTED_PLAN_ID:
        findings.append("PREDECESSOR_PLAN_ID_CHANGED")
    if PLAN_VERSION != EXPECTED_PLAN_VERSION:
        findings.append("PLAN_VERSION_NOT_3")
    if "with persistence.transaction()" not in record_execution:
        findings.append("PER_RECORD_TRANSACTION_BOUNDARY_MISSING")
    if "selected_count=1" not in record_execution or "inserted_count=1" not in record_execution:
        findings.append("PER_RECORD_RECEIPT_CONTRACT_MISSING")
    if "canonical_spatial_point_id" not in record_progress:
        findings.append("CANONICAL_NG_SPT_ORDERING_MISSING")
    lowered = (record_progress + record_execution).lower()
    if "random.shuffle" in lowered or "random.sample" in lowered:
        findings.append("NNGLA_RANDOMIZATION_PROHIBITED")
    for token in ("preview-records", "execute-records", "record-history", "--count", "--start-ordinal"):
        if token not in cli:
            findings.append(f"CLI_CONTRACT_MISSING:{token}")
    if len(manifest["migrations"]) != 18 or max(row["sequence_number"] for row in manifest["migrations"]) != 18:
        findings.append("UNEXPECTED_SCHEMA_MIGRATION_CATALOGUE_CHANGE")
    if not predecessor.is_file():
        findings.append("BUNDLE17_1MR_PREDECESSOR_QUALIFICATION_MISSING")

    return {
        "ok": not findings,
        "plan_id": PLAN_ID,
        "plan_version": PLAN_VERSION,
        "source_order": "CANONICAL_NG_SPT_ORDINAL",
        "record_atomicity": True,
        "per_record_receipt": True,
        "randomization": False,
        "repository_migration_count": len(manifest["migrations"]),
        "predecessor_qualification_present": predecessor.is_file(),
        "findings": findings,
        "database_writes": 0,
    }


def _receipt_state(connection, database_name: str, environment_name: str) -> dict:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT plan_version,count(*),coalesce(sum(selected_count),0),coalesce(sum(inserted_count),0),"
            "coalesce(sum(reused_count),0),coalesce(sum(failed_count),0) "
            "FROM geography.nngla_execution_receipt "
            "WHERE plan_id=%s AND database_name=%s AND environment_name=%s "
            "GROUP BY plan_version ORDER BY plan_version",
            (PLAN_ID, database_name, environment_name),
        )
        by_version = [
            {
                "plan_version": int(row[0]),
                "receipt_count": int(row[1]),
                "selected_count": int(row[2]),
                "inserted_count": int(row[3]),
                "reused_count": int(row[4]),
                "failed_count": int(row[5]),
            }
            for row in cur.fetchall()
        ]
        cur.execute(
            "SELECT fingerprint_sha256,count(*) FROM geography.nngla_execution_receipt "
            "WHERE database_name=%s AND environment_name=%s "
            "GROUP BY fingerprint_sha256 HAVING count(*)>1",
            (database_name, environment_name),
        )
        duplicates = [
            {"fingerprint": str(row[0]), "count": int(row[1])}
            for row in cur.fetchall()
        ]
    return {"by_plan_version": by_version, "duplicate_target_fingerprints": duplicates, "database_writes": 0}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--start-ordinal", type=int)
    parser.add_argument("--report")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()

    static = _static(root)
    result = {
        "milestone": "P006.7.11.7 Bundle 17.1.0MR",
        "purpose": "Deterministic Record-Atomic Coordinate Migration, Selectable Windows, Idempotent Recheck & PostgreSQL Resume",
        "static": static,
        "live": None,
        "ready_for_record_migration": bool(static["ok"]),
        "database_writes": 0,
    }

    connection = None
    try:
        if args.live:
            target = MigrationDatabaseTarget.from_environment(os.environ)
            password = getpass.getpass(f"Password for user {target.username}: ")
            connection = build_psycopg_connection_factory(target, password)()
            preflight = inspect_preflight(root, connection, target.environment.value)
            repository = PostgreSQLSpatialRepository(connection)
            preview = build_record_preview(
                repository,
                database_name=target.database_name,
                environment_name=target.environment.value,
                repository_revision=_revision(root),
                requested_count=args.count,
                start_ordinal=args.start_ordinal,
            )
            receipts = _receipt_state(connection, target.database_name, target.environment.value)
            observations = RecordAtomicPersistence(repository).record_receipt_observations(
                plan_id=PLAN_ID,
                plan_version=PLAN_VERSION,
                database_name=target.database_name,
                environment_name=target.environment.value,
            )
            result["live"] = {
                "preflight": {**asdict(preflight), "ready": preflight.ready},
                "preview": {
                    "requested_count": preview.requested_count,
                    "selected_count": preview.selected_count,
                    "insert_count": preview.insert_count,
                    "reuse_count": preview.reuse_count,
                    "conflict_count": preview.conflict_count,
                    "migration_complete": preview.migration_complete,
                    "execution_ready": preview.execution_ready,
                    "progress": asdict(preview.progress),
                    "window": None if preview.window is None else asdict(preview.window),
                    "authorization_fingerprint": preview.fingerprint,
                    "database_writes": 0,
                },
                "record_receipt_observation_count": len(observations),
                "receipts": receipts,
            }
            result["ready_for_record_migration"] = bool(
                static["ok"]
                and preflight.ready
                and preview.execution_ready
                and preview.conflict_count == 0
                and not receipts["duplicate_target_fingerprints"]
            )

        payload = json.dumps(result, indent=2, default=str, sort_keys=True)
        if args.report:
            report_path = Path(args.report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(payload + "\n", encoding="utf-8")
        print(payload)
        return 0 if result["ready_for_record_migration"] else 2
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
