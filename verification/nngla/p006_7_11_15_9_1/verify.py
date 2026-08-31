"""Verify published MUNICIPALITY subset for one REGION; fabric may be PARTIAL."""
from __future__ import annotations
import argparse
from .common import connect_postgresql, write_json


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--region", required=True)
    p.add_argument("--require-complete", action="store_true")
    a = p.parse_args(argv)
    c = connect_postgresql()
    try:
        with c.cursor() as cur:
            cur.execute("""
                SELECT count(*),bool_and(qualification_status='QUALIFIED'),
                       bool_and(publication_status='PUBLISHED')
                FROM geography.nngla_municipality_public_read_v2
                WHERE parent_region_id=%s
            """, (a.region,))
            row = cur.fetchone()
            cur.execute("""
                SELECT fabric_status,observed_municipality_count,
                       symmetric_difference_m2,
                       municipality_sibling_positive_overlap_m2,
                       city_municipality_positive_overlap_m2
                FROM geography.nngla_municipality_fabric_status_read_v2
                WHERE parent_region_id=%s
            """, (a.region,))
            fabric = cur.fetchone()
        count = int(row[0]) if row else 0
        qualified = True if count == 0 else bool(row[1])
        published = True if count == 0 else bool(row[2])
        if not qualified or not published:
            raise SystemExit("MUNICIPALITY public subset verification failed")
        if a.require_complete and count != 3:
            raise SystemExit("MUNICIPALITY completeness target not reached")
        payload = {
            "entity": "MUNICIPALITY",
            "regionId": a.region,
            "publicCount": count,
            "targetCount": 3,
            "status": "COMPLETE" if count == 3 else ("PARTIAL" if count else "EMPTY"),
        }
        if fabric:
            payload["fabricStatus"] = str(fabric[0])
            payload["fabricObservedCount"] = int(fabric[1])
            payload["fabricSymmetricDifferenceM2"] = float(fabric[2])
            payload["fabricSiblingOverlapM2"] = float(fabric[3])
            payload["fabricCityOverlapM2"] = float(fabric[4])
        write_json(payload)
        return 0
    finally:
        c.close()


if __name__ == "__main__":
    raise SystemExit(main())
