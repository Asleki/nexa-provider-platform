"""Read-only incremental CITY_DISTRICT preview for one published CITY."""
from __future__ import annotations
import argparse
from .common import connect_postgresql, service, write_json


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--city", required=True)
    p.add_argument("--environment-name", default="development")
    p.add_argument("--effective-date", default="")
    p.add_argument("--repository-revision", default="")
    p.add_argument("--output", default="")
    a = p.parse_args(argv)
    c = connect_postgresql()
    try:
        plan = service(c, environment_name=a.environment_name,
                       effective_date=a.effective_date or None,
                       revision=a.repository_revision.strip() or None).preview_city(a.city)
        write_json(plan.as_dict(), a.output or None)
        return 0
    finally:
        c.close()

if __name__ == "__main__":
    raise SystemExit(main())
