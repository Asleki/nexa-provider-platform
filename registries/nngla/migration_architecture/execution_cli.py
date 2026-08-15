"""Terminal interface for governed NNGLA previews, execution, verification and history."""
from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
from dataclasses import asdict

from database.migration_control.connection import (
    MigrationDatabaseTarget,
    build_psycopg_connection_factory,
)

from .execution import ExecutionRequest, ExecutionService, confirmation_token
from .persistence import PostgreSQLExecutionRepository
from .selectors import Selector, SelectorKind
from .verification import verify_receipt


def _revision():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return "UNRESOLVED"


def _repo():
    target = MigrationDatabaseTarget.from_environment(os.environ)
    password = getpass.getpass(f"Password for user {target.username}: ")
    conn = build_psycopg_connection_factory(target, password)()
    return (
        conn,
        PostgreSQLExecutionRepository(
            conn,
            database_name=target.database_name,
            environment_name=target.environment.value,
        ),
    )


def _selector(args):
    field = getattr(args, "field", None)
    equals = getattr(args, "equals", None)
    in_values = getattr(args, "in_values", None)
    exact_ids = tuple(getattr(args, "exact_id", None) or ())
    after_id = getattr(args, "after_id", None)
    limit = getattr(args, "limit", None)

    modes = sum(
        (
            equals is not None,
            bool(in_values),
            bool(exact_ids),
        )
    )

    if modes > 1:
        raise ValueError(
            "--equals, --in and --exact-id are mutually exclusive selector modes"
        )

    if field and modes == 0:
        raise ValueError("--field requires --equals or --in")

    if equals is not None:
        if not field:
            raise ValueError("--equals requires --field")
        return Selector(
            kind=SelectorKind.FIELD_EQUALS,
            field=field,
            values=(equals,),
            after_id=after_id,
            limit=limit,
        )

    if in_values:
        if not field:
            raise ValueError("--in requires --field")
        return Selector(
            kind=SelectorKind.FIELD_IN,
            field=field,
            values=tuple(in_values),
            after_id=after_id,
            limit=limit,
        )

    if exact_ids:
        if field:
            raise ValueError("--field cannot be combined with --exact-id")
        return Selector(
            kind=SelectorKind.EXACT_IDS,
            exact_ids=exact_ids,
            after_id=after_id,
            limit=limit,
        )

    if after_id or limit:
        return Selector(
            after_id=after_id,
            limit=limit,
        )

    return None


def _add_selector_arguments(parser):
    parser.add_argument("--limit", type=int)
    parser.add_argument("--after-id")
    parser.add_argument(
        "--field",
        help="Source payload field used by --equals or --in.",
    )

    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--equals",
        help="Select records whose --field value exactly equals this value.",
    )
    modes.add_argument(
        "--in",
        dest="in_values",
        nargs="+",
        metavar="VALUE",
        help="Select records whose --field value is one of these values.",
    )
    modes.add_argument(
        "--exact-id",
        action="append",
        help="Select an exact governed source record ID. May be repeated.",
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    for name in ("preview", "execute"):
        command = sub.add_parser(name)
        command.add_argument("--plan", required=True)
        _add_selector_arguments(command)

    execute = sub.choices["execute"]
    execute.add_argument("--fingerprint", required=True)
    execute.add_argument("--submitter", required=True)
    execute.add_argument("--approver", required=True)

    sub.add_parser("history")

    args = parser.parse_args(argv)

    try:
        selector = None if args.cmd == "history" else _selector(args)
    except ValueError as exc:
        parser.error(str(exc))

    conn, repo = _repo()

    try:
        service = ExecutionService(repo)

        if args.cmd == "history":
            print(
                json.dumps(
                    [list(row) for row in repo.history()],
                    indent=2,
                    default=str,
                )
            )
            return 0

        revision = _revision()

        preview = service.preview_for_execution(
            args.plan,
            selector_override=selector,
            repository_revision=revision,
        )

        token = confirmation_token(
            args.plan,
            preview.database_name,
            preview.fingerprint,
        )

        if args.cmd == "preview":
            print(
                json.dumps(
                    {
                        "plan_id": preview.plan_id,
                        "selected_count": preview.selected_count,
                        "qualification_counts": dict(
                            preview.qualification_counts
                        ),
                        "schema_ready": preview.schema_ready,
                        "execution_ready": preview.execution_ready,
                        "fingerprint": preview.fingerprint,
                        "confirmation_token": token,
                        "database_writes": 0,
                    },
                    indent=2,
                )
            )
            return 0

        confirmation = input(
            f"Type exact confirmation token:\n{token}\n> "
        )

        receipt = service.run(
            ExecutionRequest(
                args.plan,
                revision,
                args.submitter,
                args.approver,
                args.fingerprint,
                confirmation,
                selector,
            )
        )

        report = verify_receipt(receipt)

        print(
            json.dumps(
                {
                    "receipt": asdict(receipt),
                    "verification": asdict(report),
                },
                indent=2,
                default=str,
            )
        )

        return 0 if report.passed else 2

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
