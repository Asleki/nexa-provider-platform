"""Read-only Bundle 16A architecture-audit command."""
from __future__ import annotations

import json

from .audit import ArchitectureAuditor


def main() -> int:
    report = ArchitectureAuditor().audit()
    payload = {
        "name_migration_files": list(report.name_migration_files),
        "nngla_schema_files": list(report.nngla_schema_files),
        "blocking_count": len(report.blocking_findings),
        "findings": [
            {
                "code": finding.code,
                "severity": finding.severity,
                "subject": finding.subject,
                "detail": finding.detail,
            }
            for finding in report.findings
        ],
        "database_writes": 0,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
