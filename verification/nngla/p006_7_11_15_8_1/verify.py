#!/usr/bin/env python3
"""Read-only verification of committed CITY containment/publication state."""
from __future__ import annotations

import argparse
from contextlib import contextmanager

from infrastructure.database.read.nngla_city_public_map import PostgreSQLCityPublicMapRepository

from .common import connect_postgresql, write_json


class _ConnectionPoolAdapter:
    def __init__(self, connection):
        self.connection_ref = connection

    @contextmanager
    def connection(self, read_only=False):
        yield self.connection_ref


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--city", required=True)
    value.add_argument("--runtime-mode", default="production", choices=("simulation", "production"))
    return value


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    connection = connect_postgresql()
    try:
        with connection.transaction():
            connection.execute("SET TRANSACTION READ ONLY")
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT qualification_id,administrative_area_id,city_geometry_id,
                           parent_region_id,parent_region_geometry_id,
                           qualification_status,qualification_basis_code,
                           qualification_policy_version,normalized_strict_covered,
                           normalized_outside_parent_m2,normalized_outside_parent_ratio
                    FROM geography.nngla_city_parent_containment_read_v1
                    WHERE administrative_area_id=%s
                      AND effective_to IS NULL
                    """,
                    (args.city,),
                )
                rows = list(cursor.fetchall())
            if len(rows) != 1:
                raise RuntimeError(f"CITY containment qualification is not uniquely visible: {args.city}")
            row = rows[0]
            qualified = str(row[5]) == "QUALIFIED"
            repo = PostgreSQLCityPublicMapRepository(
                _ConnectionPoolAdapter(connection),
                runtime_mode=args.runtime_mode,
            )
            item = repo.get_subject(args.city)
            if qualified and item is None:
                raise RuntimeError("qualified CITY is not exposed by locked .15.7 public-map adapter")
            if not qualified and item is not None:
                raise RuntimeError("rejected CITY is unexpectedly exposed by public-map adapter")
            payload = {
                "status": "VERIFIED",
                "cityId": str(row[1]),
                "qualificationId": str(row[0]),
                "cityGeometryId": str(row[2]),
                "parentRegionId": str(row[3]),
                "parentRegionGeometryId": str(row[4]),
                "qualificationStatus": str(row[5]),
                "qualificationBasisCode": str(row[6]),
                "qualificationPolicyVersion": int(row[7]),
                "normalizedStrictCovered": bool(row[8]),
                "normalizedOutsideParentM2": float(row[9]),
                "normalizedOutsideParentRatio": float(row[10]),
                "publicMapVisible": item is not None,
                "readRuntime": args.runtime_mode,
            }
        write_json(payload)
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
