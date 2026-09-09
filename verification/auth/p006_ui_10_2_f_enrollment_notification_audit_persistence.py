"""P006.UI.10.2.F enrollment notification/mail/audit persistence qualification CLI.

This command is qualification/read oriented. Migration writes remain exclusively
under the existing ``python -m database.migration_control apply`` authority.
Mail rendering/transmission, provider credentials, report generation/upload,
public report URLs and account activation are intentionally absent from F.
"""
from __future__ import annotations

import argparse
from getpass import getpass
import json
import os
from pathlib import Path
import sys

_HERE = Path(__file__).resolve()
for _candidate in [_HERE.parent, *_HERE.parents]:
    if (_candidate / "backend").is_dir() and (_candidate / "database").is_dir():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break
else:
    raise RuntimeError("repository root not found for imports")

from backend.auth.enrollment_notification_audit_persistence import (
    GovernedEnrollmentNotificationAuditPersistenceService,
    PostgreSQLEnrollmentNotificationAuditQualification,
)


def repository_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "database" / "migrations" / "migration_manifest.json").is_file():
            return candidate
    raise RuntimeError("repository root not found")


def _settings():
    from infrastructure.database.runtime.settings import DatabaseRuntimeSettings

    values = dict(os.environ)
    if not values.get("PGPASSWORD"):
        values["PGPASSWORD"] = getpass("PostgreSQL password: ")
    return DatabaseRuntimeSettings.from_mapping(values)


def _service(root: Path):
    from infrastructure.database.runtime.pool import PostgreSQLPool

    pool = PostgreSQLPool(_settings())
    pool.open()
    qualification = PostgreSQLEnrollmentNotificationAuditQualification(pool)
    return GovernedEnrollmentNotificationAuditPersistenceService(root, qualification), pool


def _emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _base_payload(operation: str) -> dict[str, object]:
    return {
        "milestone": "P006.UI.10.2.F",
        "operation": operation,
        "migrationWritePerformed": False,
        "mailRendered": False,
        "mailSent": False,
        "mailProviderCredentialPersisted": False,
        "renderedMailBodyPersisted": False,
        "auditArtifactGenerated": False,
        "auditArtifactUploaded": False,
        "publicAuditUrlActivated": False,
        "rawCredentialMaterialPersisted": False,
        "accountActivationOperationPerformed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="P006.UI.10.2.F enrollment notification/mail/audit persistence qualification"
    )
    parser.add_argument("command", choices=("preflight", "verify", "adapter-proof"))
    parser.add_argument("--repository-root", type=Path, default=None)
    parser.add_argument("--expected-database", default="npp_dev")
    args = parser.parse_args(argv)

    root = (args.repository_root or repository_root()).resolve()
    service, pool = _service(root)
    try:
        if args.command == "preflight":
            report = service.preflight(expected_database=args.expected_database)
            payload = _base_payload("preflight")
            payload["database"] = report.safe_summary()
            _emit(payload)
            return 0
        if args.command == "verify":
            report = service.verify(expected_database=args.expected_database)
            payload = _base_payload("verify")
            payload["database"] = report.safe_summary()
            _emit(payload)
            return 0

        before, receipt, after = service.qualify_adapter(
            expected_database=args.expected_database
        )
        payload = _base_payload("adapter-proof")
        payload.update(
            {
                "before": before.safe_summary(),
                "adapter": receipt.safe_summary(),
                "after": after.safe_summary(),
                "syntheticAuthorityRolledBack": receipt.rollback_verified,
            }
        )
        _emit(payload)
        return 0
    finally:
        pool.close()


if __name__ == "__main__":
    raise SystemExit(main())
