"""CLI entry point for P006.7.11.15.1 live parity qualification."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

from infrastructure.database import DatabaseRuntimeSettings, PostgreSQLPool
from .parity import Bundle22BParityVerifier

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Bundle 22B live RDS parity qualification")
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--runtime", default=os.environ.get("INFRA_NNGLA_READ_RUNTIME", "simulation"))
    parser.add_argument("--repository-revision", default=os.environ.get("NPP_REPOSITORY_REVISION", "unknown"))
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    settings = DatabaseRuntimeSettings.from_mapping(os.environ)
    pool = PostgreSQLPool(settings)
    pool.open()
    try:
        report = Bundle22BParityVerifier(pool, repository_root=Path(args.repository_root), runtime_mode=args.runtime).qualify(repository_revision=args.repository_revision)
    finally:
        pool.close()
    rendered = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["overallStatus"] == "PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
