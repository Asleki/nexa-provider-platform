"""Governed atomic writer for one COMPLETE REGION MUNICIPALITY fabric."""
from __future__ import annotations

import argparse
from .common import connect_postgresql, service, write_json


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", required=True)
    parser.add_argument("--approved-fingerprint", required=True)
    parser.add_argument("--confirmation", required=True)
    parser.add_argument("--submitter-actor-id", required=True)
    parser.add_argument("--approver-actor-id", required=True)
    parser.add_argument("--environment-name", default="development")
    parser.add_argument("--effective-date", default="")
    parser.add_argument("--repository-revision", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)
    connection = connect_postgresql()
    try:
        result = service(
            connection,
            environment_name=args.environment_name,
            effective_date=args.effective_date or None,
            revision=args.repository_revision.strip() or None,
        ).execute_region(
            args.region,
            approved_fingerprint=args.approved_fingerprint,
            confirmation=args.confirmation,
            submitter_actor_id=args.submitter_actor_id,
            approver_actor_id=args.approver_actor_id,
        )
        write_json(result.as_dict(), args.output or None)
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
