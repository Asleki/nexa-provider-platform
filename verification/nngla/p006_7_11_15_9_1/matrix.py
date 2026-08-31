"""Read-only national MUNICIPALITY qualification matrix; one REGION at a time."""
from __future__ import annotations

import argparse
from .common import connect_postgresql, service, write_json

REGIONS = tuple(f"NG-ADM-{number:06d}" for number in range(1, 9))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment-name", default="development")
    parser.add_argument("--effective-date", default="")
    parser.add_argument("--repository-revision", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args(argv)
    connection = connect_postgresql()
    items = []
    try:
        for region_id in REGIONS:
            try:
                with connection.transaction():
                    connection.execute("SET TRANSACTION READ ONLY")
                    plan = service(
                        connection,
                        environment_name=args.environment_name,
                        effective_date=args.effective_date or None,
                        revision=args.repository_revision.strip() or None,
                    ).preview_region(region_id)
                items.append(
                    {
                        "regionId": region_id,
                        "regionName": plan.parent_region_name,
                        "status": plan.partition["partition_status"],
                        "municipalityCount": len(plan.municipalities),
                        "fingerprint": plan.fingerprint,
                        "confirmationToken": plan.confirmation_token,
                        "partition": plan.partition,
                    }
                )
            except Exception as exc:
                connection.rollback()
                items.append(
                    {"regionId": region_id, "status": "ERROR", "error": str(exc)}
                )
        payload = {
            "regionCount": 8,
            "completeCount": sum(item["status"] == "COMPLETE" for item in items),
            "incompleteCount": sum(item["status"] == "INCOMPLETE" for item in items),
            "errorCount": sum(item["status"] == "ERROR" for item in items),
            "items": items,
        }
        write_json(payload, args.output or None)
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
