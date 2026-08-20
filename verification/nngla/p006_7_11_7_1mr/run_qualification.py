#!/usr/bin/env python3
"""Read-only qualification for Bundle 17.1MR receipt compatibility and resume repair.

Static mode proves predecessor lineage and the repaired receipt-identity contract.
Live mode inspects PostgreSQL, reports the current 0/2411 or 11/2400-style
resume state, and checks existing plan receipts without performing writes.
Final mode additionally runs the existing 2,411-point final verifier.
"""
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
from registries.nngla.migration_ready.catalogue import load_batch_profiles
from registries.nngla.migration_ready.orchestrator import (
    PLAN_ID,
    PLAN_VERSION,
    build_spatial_preview,
)
from registries.nngla.migration_ready.preflight import inspect_preflight
from registries.nngla.migration_ready.verification import verify_migration_ready
from registries.nngla.spatial_fabric.bundle17e.persistence import PostgreSQLSpatialRepository


EXPECTED_PLAN_ID = "P006.7.11.7.0MR-SPATIAL-BATCH"
EXPECTED_PLAN_VERSION = 2
UNIQUE_INDEX_TOKEN = (
    "CREATE UNIQUE INDEX ux_nngla_execution_fingerprint_target ON "
    "geography.nngla_execution_receipt(fingerprint_sha256,database_name,environment_name);"
)


def _revision(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "UNRESOLVED"


def _static(root: Path) -> dict:
    findings: list[str] = []
    orchestrator_path = root / "registries/nngla/migration_ready/orchestrator.py"
    execution_sql_path = root / "database/migrations/m006_07_11_nngla_execution_foundation.sql"
    manifest_path = root / "database/migrations/migration_manifest.json"
    predecessor_runner = root / "verification/nngla/p006_7_11_7_0mr/run_qualification.py"

    source = orchestrator_path.read_text(encoding="utf-8")
    sql = " ".join(execution_sql_path.read_text(encoding="utf-8").split())
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    profile = load_batch_profiles()["initial-spatial-2411"]

    if PLAN_ID != EXPECTED_PLAN_ID:
        findings.append("PREDECESSOR_PLAN_ID_CHANGED")
    if PLAN_VERSION != EXPECTED_PLAN_VERSION:
        findings.append("PLAN_VERSION_NOT_2")
    if "def _batch_receipt_fingerprint(" not in source:
        findings.append("BATCH_RECEIPT_FINGERPRINT_DERIVATION_MISSING")
    if "fingerprint=batch_receipt_fingerprint" not in source:
        findings.append("BATCH_RECEIPT_FINGERPRINT_NOT_PERSISTED")
    if "fingerprint=preview.fingerprint" in source:
        findings.append("AUTHORIZATION_FINGERPRINT_STILL_REUSED_AS_RECEIPT_IDENTITY")
    if "authorization_fingerprint={preview.fingerprint}" not in source:
        findings.append("AUTHORIZATION_FINGERPRINT_AUDIT_LINK_MISSING")
    if UNIQUE_INDEX_TOKEN not in sql:
        findings.append("LOCKED_RECEIPT_UNIQUE_INDEX_CHANGED_OR_MISSING")
    if len(manifest["migrations"]) != 18 or max(row["sequence_number"] for row in manifest["migrations"]) != 18:
        findings.append("UNEXPECTED_SCHEMA_MIGRATION_CATALOGUE_CHANGE")
    if profile.batch_sizes != (11, 800, 800, 800):
        findings.append("DEFAULT_BATCH_PROFILE_CHANGED")
    if not predecessor_runner.is_file():
        findings.append("BUNDLE17_0MR_PREDECESSOR_QUALIFICATION_MISSING")

    return {
        "ok": not findings,
        "plan_id": PLAN_ID,
        "plan_version": PLAN_VERSION,
        "default_batch_profile": list(profile.batch_sizes),
        "repository_migration_count": len(manifest["migrations"]),
        "predecessor_qualification_present": predecessor_runner.is_file(),
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
            "SELECT count(*) FROM geography.nngla_execution_item i "
            "JOIN geography.nngla_execution_receipt r ON r.execution_id=i.execution_id "
            "WHERE r.plan_id=%s AND r.database_name=%s AND r.environment_name=%s",
            (PLAN_ID, database_name, environment_name),
        )
        receipt_items = int(cur.fetchone()[0])
        cur.execute(
            "SELECT fingerprint_sha256,count(*) FROM geography.nngla_execution_receipt "
            "WHERE database_name=%s AND environment_name=%s "
            "GROUP BY fingerprint_sha256 HAVING count(*)>1",
            (database_name, environment_name),
        )
        duplicate_target_fingerprints = [
            {"fingerprint": str(row[0]), "count": int(row[1])}
            for row in cur.fetchall()
        ]
    return {
        "plan_id": PLAN_ID,
        "by_plan_version": by_version,
        "receipt_item_count": receipt_items,
        "duplicate_target_fingerprints": duplicate_target_fingerprints,
        "database_writes": 0,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    parser.add_argument("--live", action="store_true", help="Read-only PostgreSQL preflight/resume inspection")
    parser.add_argument("--final-verify", action="store_true", help="Also verify completed 2,411-point migration")
    parser.add_argument("--report", help="Optional JSON report path")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()

    static = _static(root)
    result = {
        "milestone": "P006.7.11.7 Bundle 17.1MR",
        "purpose": "Migration-Ready Live Execution Compatibility & Resume Repair",
        "static": static,
        "live": None,
        "final_verification": None,
        "ready_for_resume": bool(static["ok"]),
        "migration_complete": False,
        "database_writes": 0,
    }

    connection = None
    try:
        if args.live or args.final_verify:
            target = MigrationDatabaseTarget.from_environment(os.environ)
            password = getpass.getpass(f"Password for user {target.username}: ")
            connection = build_psycopg_connection_factory(target, password)()
            preflight = inspect_preflight(root, connection, target.environment.value)
            preview = build_spatial_preview(
                PostgreSQLSpatialRepository(connection),
                database_name=target.database_name,
                environment_name=target.environment.value,
                repository_revision=_revision(root),
            )
            receipts = _receipt_state(connection, target.database_name, target.environment.value)
            receipt_versions_valid = all(
                row["plan_version"] in {1, 2} for row in receipts["by_plan_version"]
            )
            result["live"] = {
                "preflight": {**asdict(preflight), "ready": preflight.ready},
                "preview": {
                    "total_count": preview.total_count,
                    "insert_count": preview.insert_count,
                    "reuse_count": preview.reuse_count,
                    "conflict_count": preview.conflict_count,
                    "profile_id": preview.profile_id,
                    "authorization_fingerprint": preview.fingerprint,
                    "execution_ready": preview.execution_ready,
                    "database_writes": 0,
                },
                "receipts": receipts,
                "receipt_versions_valid": receipt_versions_valid,
            }
            result["ready_for_resume"] = bool(
                static["ok"]
                and preflight.ready
                and preview.execution_ready
                and preview.conflict_count == 0
                and not receipts["duplicate_target_fingerprints"]
                and receipt_versions_valid
            )

            if args.final_verify:
                verification = verify_migration_ready(
                    root,
                    connection,
                    database_name=target.database_name,
                    environment_name=target.environment.value,
                )
                result["final_verification"] = {**asdict(verification), "passed": verification.passed}
                result["migration_complete"] = verification.passed

        payload = json.dumps(result, indent=2, default=str, sort_keys=True)
        if args.report:
            report_path = Path(args.report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(payload + "\n", encoding="utf-8")
        print(payload)
        ok = result["migration_complete"] if args.final_verify else result["ready_for_resume"]
        return 0 if ok else 2
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
