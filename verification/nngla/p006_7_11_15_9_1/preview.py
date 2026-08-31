"""Read-only governed preview for one REGION's MUNICIPALITY fabric."""
from __future__ import annotations

import argparse
from .common import connect_postgresql, service, write_json


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", required=True)
    parser.add_argument("--environment-name", default="development")
    parser.add_argument("--effective-date", default="")
    parser.add_argument("--repository-revision", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)
    connection = connect_postgresql()
    try:
        with connection.transaction():
            connection.execute("SET TRANSACTION READ ONLY")
            plan = service(
                connection,
                environment_name=args.environment_name,
                effective_date=args.effective_date or None,
                revision=args.repository_revision.strip() or None,
            ).preview_region(args.region)
        write_json(plan.as_dict(), args.output or None)
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
