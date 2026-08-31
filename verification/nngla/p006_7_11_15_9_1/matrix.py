"""Read-only national MUNICIPALITY feature/fabric matrix."""
from __future__ import annotations
import argparse
from .common import connect_postgresql, write_json
REGIONS = tuple(f"NG-ADM-{number:06d}" for number in range(1, 9))

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", default="")
    a = p.parse_args(argv)
    c = connect_postgresql()
    try:
        items = []
        with c.cursor() as cur:
            for region_id in REGIONS:
                cur.execute("SELECT count(*) FROM geography.nngla_municipality_public_read_v2 WHERE parent_region_id=%s", (region_id,))
                public_count = int(cur.fetchone()[0])
                cur.execute("SELECT fabric_status,observed_municipality_count,symmetric_difference_m2 FROM geography.nngla_municipality_fabric_status_read_v2 WHERE parent_region_id=%s", (region_id,))
                f = cur.fetchone()
                items.append({
                    "regionId": region_id,
                    "publicCount": public_count,
                    "publicationStatus": "COMPLETE" if public_count == 3 else ("PARTIAL" if public_count else "EMPTY"),
                    "fabricStatus": str(f[0]) if f else "UNKNOWN",
                    "fabricObservedCount": int(f[1]) if f else 0,
                    "fabricSymmetricDifferenceM2": float(f[2]) if f else None,
                })
        payload = {
            "regionCount": 8,
            "publicMunicipalityCount": sum(i["publicCount"] for i in items),
            "completeFabricCount": sum(i["fabricStatus"] == "COMPLETE" for i in items),
            "partialFabricCount": sum(i["fabricStatus"] == "PARTIAL" for i in items),
            "items": items,
        }
        write_json(payload, a.output or None)
        return 0
    finally:
        c.close()

if __name__ == "__main__":
    raise SystemExit(main())
