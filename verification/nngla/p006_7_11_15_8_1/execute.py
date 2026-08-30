#!/usr/bin/env python3
"""Explicit writer for one approved CITY containment qualification plan."""
from __future__ import annotations

import argparse

from .common import connect_postgresql, service, write_json


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--city", required=True)
    value.add_argument("--environment-name", default="dev")
    value.add_argument("--effective-date", required=True)
    value.add_argument("--repository-revision", default="")
    value.add_argument("--approved-fingerprint", required=True)
    value.add_argument("--confirmation", required=True)
    value.add_argument("--submitter", required=True)
    value.add_argument("--approver", required=True)
    value.add_argument("--execute", action="store_true")
    return value


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if not args.execute:
        raise SystemExit("REFUSED: --execute is required after reviewing a fresh read-only containment preview")
    connection = connect_postgresql()
    try:
        result = service(
            connection,
            environment_name=args.environment_name,
            effective_date=args.effective_date,
            revision=args.repository_revision.strip() or None,
        ).execute(
            args.city,
            approved_fingerprint=args.approved_fingerprint,
            confirmation=args.confirmation,
            submitter_actor_id=args.submitter,
            approver_actor_id=args.approver,
        )
        write_json(result.as_dict())
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
