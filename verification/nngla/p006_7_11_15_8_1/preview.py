#!/usr/bin/env python3
"""Read-only preview of one deterministic CITY containment qualification."""
from __future__ import annotations

import argparse

from .common import connect_postgresql, service, write_json


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--city", required=True)
    value.add_argument("--environment-name", default="dev")
    value.add_argument("--effective-date", default="")
    value.add_argument("--repository-revision", default="")
    value.add_argument("--output", default="")
    return value


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    connection = connect_postgresql()
    try:
        with connection.transaction():
            connection.execute("SET TRANSACTION READ ONLY")
            plan = service(
                connection,
                environment_name=args.environment_name,
                effective_date=args.effective_date or None,
                revision=args.repository_revision.strip() or None,
            ).preview(args.city)
        write_json(plan.as_dict(), args.output or None)
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
