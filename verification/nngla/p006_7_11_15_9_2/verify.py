"""Verify currently published CITY_DISTRICT subset; completeness is separate."""
from __future__ import annotations
import argparse
from .common import connect_postgresql, write_json


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--require-complete", action="store_true")
    a = p.parse_args(argv)
    c = connect_postgresql()
    try:
        with c.cursor() as cur:
            cur.execute("""
                SELECT count(*),count(DISTINCT parent_city_id),
                       bool_and(qualification_status='QUALIFIED'),
                       bool_and(publication_status='PUBLISHED')
                FROM geography.nngla_city_district_public_read_v2
            """)
            row = cur.fetchone()
            cur.execute("""
                SELECT fabric_status,count(*)
                FROM geography.nngla_city_district_fabric_status_read_v2
                GROUP BY fabric_status ORDER BY fabric_status
            """)
            fabrics = {str(k): int(v) for k, v in cur.fetchall()}
        count = int(row[0]) if row else 0
        parents = int(row[1]) if row else 0
        qualified = True if count == 0 else bool(row[2])
        published = True if count == 0 else bool(row[3])
        if not qualified or not published:
            raise SystemExit("CITY_DISTRICT public subset verification failed")
        if a.require_complete and (count, parents) != (64, 8):
            raise SystemExit("CITY_DISTRICT completeness target not reached")
        write_json({
            "entity": "CITY_DISTRICT",
            "publicCount": count,
            "parentCityCount": parents,
            "targetCount": 64,
            "fabricStatusCounts": fabrics,
            "status": "COMPLETE" if count == 64 else ("PARTIAL" if count else "EMPTY"),
        })
        return 0
    finally:
        c.close()


if __name__ == "__main__":
    raise SystemExit(main())
