"""P006.UI.10.2.B governed Enigma catalogue qualification/admission operator command.

Private source rows are read at execution time and are never printed. The only
write command is ``admit`` and it requires an explicit confirmation token.
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

from backend.auth.enigma_catalogue_admission import (
    GovernedEnigmaCatalogueService,
    PostgreSQLEnigmaCatalogueAdmission,
)
ADMISSION_CONFIRMATION = "P006.UI.10.2.B-ADMIT-279"


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


def _database_service(root: Path):
    from infrastructure.database.runtime.pool import PostgreSQLPool

    pool = PostgreSQLPool(_settings())
    pool.open()
    authority = PostgreSQLEnigmaCatalogueAdmission(pool)
    return GovernedEnigmaCatalogueService(root, authority), pool


def _source_summaries(sources) -> list[dict[str, object]]:
    return [source.safe_summary() for source in sources]


def _emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="P006.UI.10.2.B governed Enigma catalogue qualification/admission"
    )
    parser.add_argument(
        "command",
        choices=("qualify", "preflight", "admit", "verify", "adapter-proof"),
    )
    parser.add_argument("--repository-root", type=Path, default=None)
    parser.add_argument("--expected-database", default="npp_dev")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)

    root = (args.repository_root or repository_root()).resolve()

    if args.command == "qualify":
        service = GovernedEnigmaCatalogueService(root)
        sources = service.qualify_sources()
        _emit(
            {
                "milestone": "P006.UI.10.2.B",
                "operation": "qualify",
                "qualified": True,
                "catalogueFamilies": _source_summaries(sources),
                "sharedChallengeRowTotal": sum(source.row_count for source in sources),
                "privateResponseMaterialPrinted": False,
            }
        )
        return 0

    service, pool = _database_service(root)
    try:
        if args.command == "preflight":
            sources = service.qualify_sources()
            report = service.preflight(
                expected_database=args.expected_database,
                require_empty_catalogue_authority=False,
            )
            _emit(
                {
                    "milestone": "P006.UI.10.2.B",
                    "operation": "preflight",
                    "sources": _source_summaries(sources),
                    "database": report.safe_summary(),
                }
            )
            return 0

        if args.command == "admit":
            if args.confirm != ADMISSION_CONFIRMATION:
                parser.error(
                    f"admit requires --confirm {ADMISSION_CONFIRMATION}"
                )
            sources, preflight, admission, read_back, postflight = service.admit(
                expected_database=args.expected_database,
            )
            _emit(
                {
                    "milestone": "P006.UI.10.2.B",
                    "operation": "admit",
                    "sources": _source_summaries(sources),
                    "preflight": preflight.safe_summary(),
                    "admission": admission.safe_summary(),
                    "readBack": read_back.safe_summary(),
                    "postflight": postflight.safe_summary(),
                    "privateResponseMaterialPrinted": False,
                }
            )
            return 0

        if args.command == "verify":
            sources, preflight, read_back = service.verify(
                expected_database=args.expected_database,
            )
            _emit(
                {
                    "milestone": "P006.UI.10.2.B",
                    "operation": "verify",
                    "sources": _source_summaries(sources),
                    "preflight": preflight.safe_summary(),
                    "readBack": read_back.safe_summary(),
                    "privateResponseMaterialPrinted": False,
                }
            )
            return 0

        sources, preflight, adapter = service.qualify_adapter(
            expected_database=args.expected_database,
        )
        _emit(
            {
                "milestone": "P006.UI.10.2.B",
                "operation": "adapter-proof",
                "sources": _source_summaries(sources),
                "preflight": preflight.safe_summary(),
                "adapter": adapter.safe_summary(),
                "privateResponseMaterialPrinted": False,
            }
        )
        return 0
    finally:
        pool.close()


if __name__ == "__main__":
    raise SystemExit(main())
