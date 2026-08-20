#!/usr/bin/env python3
"""Bundle 17.0MR qualification runner.

Static mode proves source/configuration locks without touching PostgreSQL. Live
mode performs read-only preflight and spatial preview. Final mode additionally
verifies that the actual 2,411-point migration is complete. This runner never
executes migration writes.
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
from registries.nngla.migration_ready.candidate_state import assess_candidate_state
from registries.nngla.migration_ready.catalogue import load_batch_profiles, load_domain_plan
from registries.nngla.migration_ready.empty_registers import assess_empty_registers, empty_registers_ready
from registries.nngla.migration_ready.orchestrator import build_spatial_preview
from registries.nngla.migration_ready.preflight import inspect_preflight
from registries.nngla.migration_ready.verification import verify_migration_ready
from registries.nngla.spatial_fabric.bundle17e.persistence import PostgreSQLSpatialRepository
from registries.nngla.spatial_fabric.bundle17e.qualification import bundle17e_is_qualified


def _revision(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "UNRESOLVED"


def _static(root: Path) -> dict:
    candidate = assess_candidate_state(root)
    empty = assess_empty_registers(root)
    profiles = load_batch_profiles()
    domain_plan = load_domain_plan()
    findings: list[str] = []
    if not bundle17e_is_qualified():
        findings.append("BUNDLE17E_QUALIFICATION_FAILED")
    if not candidate.passed:
        findings.extend(candidate.findings or ("CANDIDATE_STATE_FAILED",))
    if not empty_registers_ready(empty):
        findings.append("EMPTY_REGISTER_SOURCE_READINESS_FAILED")
    if profiles["initial-spatial-2411"].batch_sizes != (11, 800, 800, 800):
        findings.append("DEFAULT_BATCH_PROFILE_CHANGED")
    if sum(row.expected_count for row in domain_plan if row.domain_key == "spatial-points-2411") != 2411:
        findings.append("SPATIAL_DOMAIN_COUNT_CHANGED")
    return {
        "ok": not findings,
        "bundle17e_qualified": bundle17e_is_qualified(),
        "candidate_state": asdict(candidate),
        "empty_registers": [asdict(item) for item in empty],
        "default_batch_profile": list(profiles["initial-spatial-2411"].batch_sizes),
        "domain_count": len(domain_plan),
        "findings": findings,
        "database_writes": 0,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    parser.add_argument("--live", action="store_true", help="Run read-only PostgreSQL preflight and preview")
    parser.add_argument("--final-verify", action="store_true", help="Also verify completed 2,411-point migration")
    parser.add_argument("--report", help="Optional JSON report path; omitted means stdout only")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()

    static = _static(root)
    result = {
        "milestone": "P006.7.11.7 Bundle 17.0MR",
        "static": static,
        "live": None,
        "final_verification": None,
        "ready_for_live_migration": bool(static["ok"]),
        "migration_complete": False,
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
            result["live"] = {
                "preflight": {**asdict(preflight), "ready": preflight.ready},
                "preview": {
                    "database_name": preview.database_name,
                    "profile_id": preview.profile_id,
                    "total_count": preview.total_count,
                    "insert_count": preview.insert_count,
                    "reuse_count": preview.reuse_count,
                    "conflict_count": preview.conflict_count,
                    "fingerprint": preview.fingerprint,
                    "execution_ready": preview.execution_ready,
                    "database_writes": 0,
                },
            }
            result["ready_for_live_migration"] = bool(static["ok"] and preflight.ready and preview.execution_ready)

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
        ok = result["migration_complete"] if args.final_verify else result["ready_for_live_migration"]
        return 0 if ok else 2
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
