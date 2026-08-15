"""Terminal-safe Bundle 16B NNGLA plan catalogue and zero-write preview CLI."""
from __future__ import annotations

import argparse
import json

from .plans import PLAN_CATALOGUE
from .preview import PreviewService, TargetStateSnapshot
from .selectors import Selector, SelectorKind


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m registries.nngla.migration_architecture.plan_cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list-plans")
    preview = sub.add_parser("preview")
    preview.add_argument("--plan", required=True)
    preview.add_argument("--limit", type=int)
    preview.add_argument("--after-id")
    preview.add_argument("--database", default="UNRESOLVED")
    preview.add_argument("--environment", default="UNRESOLVED")
    preview.add_argument("--repository-revision", default="UNRESOLVED")
    preview.add_argument("--schema-capability", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "list-plans":
        print(json.dumps({"plans": sorted(PLAN_CATALOGUE), "database_writes": 0}, indent=2))
        return 0
    plan = PLAN_CATALOGUE[args.plan]
    selector = plan.selector
    if args.limit is not None or args.after_id is not None:
        selector = Selector(
            selector.kind,
            selector.field,
            selector.values,
            selector.exact_ids,
            args.after_id if args.after_id is not None else selector.after_id,
            args.limit if args.limit is not None else selector.limit,
        )
    target = TargetStateSnapshot(
        args.database,
        args.environment,
        frozenset(args.schema_capability),
    )
    report = PreviewService().preview(
        args.plan,
        selector_override=selector,
        target=target,
        repository_revision=args.repository_revision,
    )
    payload = {
        "plan_id": report.plan_id,
        "source_key": report.source_key,
        "source_count": report.source_count,
        "selected_count": report.selected_count,
        "qualification_counts": report.qualification_counts,
        "database": report.database_name,
        "environment": report.environment_name,
        "schema_ready": report.schema_ready,
        "execution_ready": report.execution_ready,
        "fingerprint": report.fingerprint,
        "selected_source_ids": list(report.selected_source_ids),
        "proposed_canonical_ids": list(report.proposed_canonical_ids),
        "database_writes": report.database_writes,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
