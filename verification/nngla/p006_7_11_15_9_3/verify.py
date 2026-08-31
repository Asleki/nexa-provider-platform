"""Verify currently published TOWN subset, optionally for one MUNICIPALITY."""
from __future__ import annotations
import argparse
from .common import connect_postgresql, write_json


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--municipality", default="")
    p.add_argument("--require-complete", action="store_true")
    a = p.parse_args(argv)
    c = connect_postgresql()
    try:
        where = ""
        params = ()
        if a.municipality:
            where = "WHERE parent_municipality_id=%s"
            params = (a.municipality,)
        with c.cursor() as cur:
            cur.execute(f"""
                SELECT count(*),count(DISTINCT parent_municipality_id),
                       bool_and(source_qualification_status='QUALIFIED_CANDIDATE_NOT_LEGAL_BOUNDARY'),
                       bool_and(legal_boundary_status='NOT_ADMINISTRATIVE_OR_LEGAL_BOUNDARY'),
                       bool_and(qualification_status='QUALIFIED'),
                       bool_and(publication_status='PUBLISHED')
                FROM geography.nngla_town_public_read_v2
                {where}
            """, params)
            row = cur.fetchone()
        count = int(row[0]) if row else 0
        parent_count = int(row[1]) if row else 0
        checks = [True, True, True, True] if count == 0 else [bool(v) for v in row[2:6]]
        if not all(checks):
            raise SystemExit("TOWN public subset verification failed")
        target = 5 if a.municipality else 120
        if a.require_complete and count != target:
            raise SystemExit("TOWN completeness target not reached")
        write_json({
            "entity": "TOWN",
            "municipalityId": a.municipality or None,
            "publicCount": count,
            "parentMunicipalityCount": parent_count,
            "targetCount": target,
            "status": "COMPLETE" if count == target else ("PARTIAL" if count else "EMPTY"),
        })
        return 0
    finally:
        c.close()


if __name__ == "__main__":
    raise SystemExit(main())
