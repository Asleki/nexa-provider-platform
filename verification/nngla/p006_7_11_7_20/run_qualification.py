#!/usr/bin/env python3
"""P006.7.11.7.20 NNGLA operational-backend closure qualification runner.

This file is verification support, not production implementation.  Bundle 17P is a
no-new-code closure gate: it inspects and exercises the capabilities delivered by
Bundles 17A-17O without introducing a new NNGLA domain implementation.

The runner performs deterministic repository/static checks itself and can execute
existing repository integration commands supplied by the operator through CLI
arguments or environment variables.  It never invents or silently substitutes a
new command path for the repository's existing governed command services.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from typing import Iterable

REQUIRED_SURFACES = (
    "registries/nngla",
    "database/migrations",
    "data/novegeo/nngla",
    "tests",
)

BUNDLE_17N_CONTRACTS = (
    "novegeo_runtime_command_catalogue_v001.csv",
    "novegeo_runtime_command_authorization_matrix_v001.csv",
    "novegeo_runtime_bulk_operation_policy_v001.csv",
    "novegeo_runtime_idempotency_policy_v001.csv",
    "novegeo_runtime_command_validation_rules_v001.csv",
)

BUNDLE_17O_CONTRACTS = (
    "novegeo_spatial_query_catalogue_v001.csv",
    "novegeo_spatial_query_result_contracts_v001.csv",
    "novegeo_read_model_definition_catalogue_v001.csv",
    "novegeo_geocoding_normalization_rules_v001.csv",
    "novegeo_cross_registry_spatial_reference_contracts_v001.csv",
)

DAY_ZERO_REGISTERS = (
    "address_reference_candidates.csv",
    "parcel_bootstrap.csv",
    "title_bootstrap.csv",
    "state_land_bootstrap.csv",
    "survey_control_point_candidates.csv",
)

VERSIONED_POPULATED_REGISTERS = (
    "address_reference_candidates_v002.csv",
    "parcel_bootstrap_v002.csv",
    "title_bootstrap_v002.csv",
    "state_land_bootstrap_v002.csv",
    "survey_control_point_candidates_v002.csv",
)

RUNTIME_CAPABILITY_GROUPS = {
    "runtime_command": ("runtime_command", "command_catalogue", "command_service"),
    "authorization": ("authorization", "authorisation", "authorized", "authorised"),
    "bulk_operation": ("bulk_operation", "bulk operation", "bulk_command"),
    "idempotency": ("idempotency", "idempotent", "idempotency_key"),
    "receipt": ("receipt", "execution_receipt", "command_receipt"),
}

SPATIAL_QUERY_CAPABILITY_GROUPS = {
    "containment": ("containment", "contains", "within"),
    "adjacency": ("adjacency", "adjacent"),
    "intersection": ("intersection", "intersects", "crosses"),
    "nearest": ("nearest", "distance"),
    "geocoding": ("geocod", "reverse_geocod"),
    "read_model": ("read_model", "read model"),
}

# Changes allowed for this qualification bundle before operator roadmap completion.
QUALIFICATION_ONLY_PREFIXES = (
    "tests/",
    "verification/",
)


def _norm(path: Path) -> str:
    return path.as_posix().lstrip("./")


def _find_named(root: Path, filename: str) -> list[str]:
    base = root / "data" / "novegeo" / "nngla"
    if not base.is_dir():
        return []
    return sorted(_norm(p.relative_to(root)) for p in base.rglob(filename) if p.is_file())


def _iter_text_files(root: Path) -> Iterable[Path]:
    roots = [
        root / "registries" / "nngla",
        root / "services",
        root / "backend",
        root / "database",
    ]
    suffixes = {".py", ".sql", ".json", ".csv", ".md", ".txt"}
    for base in roots:
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in suffixes:
                yield path


def _corpus(root: Path, *, max_bytes_per_file: int = 2_000_000) -> str:
    chunks: list[str] = []
    for path in _iter_text_files(root):
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if len(data) > max_bytes_per_file:
            data = data[:max_bytes_per_file]
        chunks.append(data.decode("utf-8", errors="ignore").lower())
    return "\n".join(chunks)


def _capability_results(corpus: str, groups: dict[str, tuple[str, ...]]) -> dict[str, dict]:
    result = {}
    for name, tokens in groups.items():
        matched = [token for token in tokens if token.lower() in corpus]
        result[name] = {"ok": bool(matched), "matched_tokens": matched}
    return result


def _git_changed_paths(root: Path) -> tuple[bool, list[str], str | None]:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        return False, [], str(exc)
    if proc.returncode != 0:
        return False, [], proc.stderr.strip() or "git status failed"
    paths = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        value = line[3:]
        # Rename format is "old -> new"; the destination is the relevant current path.
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        paths.append(value.strip().replace("\\", "/"))
    return True, sorted(paths), None


def _run_shell(label: str, command: str, root: Path) -> dict:
    started = datetime.now(timezone.utc)
    proc = subprocess.run(
        command,
        cwd=root,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    finished = datetime.now(timezone.utc)
    return {
        "label": label,
        "command": command,
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "output": proc.stdout,
    }


def run_static_checks(root: Path) -> dict:
    surfaces = {name: (root / name).is_dir() for name in REQUIRED_SURFACES}

    contracts_17n = {name: _find_named(root, name) for name in BUNDLE_17N_CONTRACTS}
    contracts_17o = {name: _find_named(root, name) for name in BUNDLE_17O_CONTRACTS}
    day_zero = {name: _find_named(root, name) for name in DAY_ZERO_REGISTERS}
    populated_v002 = {name: _find_named(root, name) for name in VERSIONED_POPULATED_REGISTERS}

    corpus = _corpus(root)
    runtime_caps = _capability_results(corpus, RUNTIME_CAPABILITY_GROUPS)
    query_caps = _capability_results(corpus, SPATIAL_QUERY_CAPABILITY_GROUPS)

    git_ok, changed, git_error = _git_changed_paths(root)
    disallowed_changes = []
    if git_ok:
        for path in changed:
            # Roadmap is intentionally not allowed to change during Phase B-E/17P qualification.
            if not any(path.startswith(prefix) for prefix in QUALIFICATION_ONLY_PREFIXES):
                disallowed_changes.append(path)

    checks = {
        "repository_surfaces": {
            "ok": all(surfaces.values()),
            "details": surfaces,
        },
        "bundle_17n_contracts": {
            "ok": all(contracts_17n.values()),
            "details": contracts_17n,
        },
        "bundle_17o_contracts": {
            "ok": all(contracts_17o.values()),
            "details": contracts_17o,
        },
        "historical_day_zero_registers_preserved": {
            "ok": all(day_zero.values()),
            "details": day_zero,
        },
        "runtime_capability_evidence": {
            "ok": all(v["ok"] for v in runtime_caps.values()),
            "details": runtime_caps,
        },
        "spatial_query_capability_evidence": {
            "ok": all(v["ok"] for v in query_caps.values()),
            "details": query_caps,
        },
        "qualification_only_worktree_changes": {
            "ok": git_ok and not disallowed_changes,
            "details": {
                "git_available": git_ok,
                "git_error": git_error,
                "changed_paths": changed,
                "disallowed_paths": disallowed_changes,
                "allowed_prefixes": list(QUALIFICATION_ONLY_PREFIXES),
            },
        },
        "v002_register_discovery": {
            # Informational. P006.7.11.7 permits these only as versioned populated successors;
            # their absence is not itself a 17P failure if the register remains legitimately empty.
            "ok": True,
            "details": populated_v002,
        },
    }
    return {
        "ok": all(item["ok"] for key, item in checks.items() if key != "v002_register_discovery"),
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run P006.7.11.7.20 no-new-code NNGLA closure qualification checks."
    )
    parser.add_argument("--repo-root", default=".", help="Canonical nexa-provider-platform repository root")
    parser.add_argument("--output", default="verification/nngla/p006_7_11_7_20/qualification_report.json")
    parser.add_argument("--static-only", action="store_true", help="Run deterministic repository checks only")
    parser.add_argument("--pytest-cmd", default=os.getenv("NPP_17P_PYTEST_CMD", ""))
    parser.add_argument("--fresh-bootstrap-cmd", default=os.getenv("NPP_17P_FRESH_BOOTSTRAP_CMD", ""))
    parser.add_argument("--future-data-cmd", default=os.getenv("NPP_17P_FUTURE_DATA_CMD", ""))
    parser.add_argument("--idempotency-cmd", default=os.getenv("NPP_17P_IDEMPOTENCY_CMD", ""))
    parser.add_argument("--receipts-cmd", default=os.getenv("NPP_17P_RECEIPTS_CMD", ""))
    args = parser.parse_args(argv)

    root = Path(args.repo_root).resolve()
    report = {
        "milestone": "P006.7.11.7.20",
        "bundle": "17P",
        "qualification_kind": "NO_NEW_PRODUCTION_CODE",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(root),
        "static": run_static_checks(root),
        "executions": [],
    }

    command_fields = [
        ("pytest_regression", args.pytest_cmd),
        ("fresh_database_bootstrap", args.fresh_bootstrap_cmd),
        ("future_data_simulation", args.future_data_cmd),
        ("idempotent_rerun", args.idempotency_cmd),
        ("receipt_verification", args.receipts_cmd),
    ]

    if not args.static_only:
        for label, command in command_fields:
            if command.strip():
                report["executions"].append(_run_shell(label, command, root))
            else:
                report["executions"].append({
                    "label": label,
                    "ok": False,
                    "status": "NOT_CONFIGURED",
                    "reason": "Use the existing repository command for this phase; 17P must not invent a new operational CLI.",
                })

    static_ok = bool(report["static"]["ok"])
    if args.static_only:
        report["lock_ready"] = False
        report["lock_ready_reason"] = "Static qualification only; fresh DB, future-data, idempotency, receipts and regressions remain operator-run gates."
        exit_code = 0 if static_ok else 1
    else:
        execution_ok = bool(report["executions"]) and all(item.get("ok") for item in report["executions"])
        report["lock_ready"] = static_ok and execution_ok
        report["lock_ready_reason"] = (
            "All configured qualification gates passed." if report["lock_ready"]
            else "One or more mandatory gates failed or were not configured."
        )
        exit_code = 0 if report["lock_ready"] else 1

    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "milestone": report["milestone"],
        "static_ok": static_ok,
        "lock_ready": report["lock_ready"],
        "report": str(output),
    }, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
