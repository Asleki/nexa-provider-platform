#!/usr/bin/env python3
"""Read-only national qualification matrix for the eight official CITY identities."""
from __future__ import annotations

import argparse

from registries.nngla.city_realization.contracts import OFFICIAL_NOVEGEO_CITY_IDS

from .common import connect_postgresql, service, write_json


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--environment-name", default="dev")
    value.add_argument("--effective-date", default="")
    value.add_argument("--repository-revision", default="")
    value.add_argument("--output", default="")
    return value


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    connection = connect_postgresql()
    rows = []
    try:
        for city_id in OFFICIAL_NOVEGEO_CITY_IDS:
            with connection.transaction():
                connection.execute("SET TRANSACTION READ ONLY")
                plan = service(
                    connection,
                    environment_name=args.environment_name,
                    effective_date=args.effective_date or None,
                    revision=args.repository_revision.strip() or None,
                ).preview(city_id)
            rows.append(
                {
                    "cityId": plan.city_id,
                    "canonicalName": plan.canonical_name,
                    "parentRegionId": plan.parent_region_id,
                    "parentRegionName": plan.parent_region_name,
                    "plannedAction": plan.planned_action,
                    "realizationMethod": plan.realization_method,
                    "qualificationStatus": plan.qualification_status,
                    "qualificationBasisCode": plan.qualification_basis_code,
                    "sourceStrictCovered": plan.source_strict_covered,
                    "sourceOutsideParentM2": plan.source_outside_parent_m2,
                    "sourceOutsideParentRatio": plan.source_outside_parent_ratio,
                    "normalizedStrictCovered": plan.normalized_strict_covered,
                    "normalizedOutsideParentM2": plan.normalized_outside_parent_m2,
                    "normalizedOutsideParentRatio": plan.normalized_outside_parent_ratio,
                    "areaRemovedM2": plan.area_removed_m2,
                    "areaRemovedRatio": plan.area_removed_ratio,
                    "geometryTypeCode": plan.geometry_type_code,
                    "cityGeometryId": plan.city_geometry_id,
                    "qualificationId": plan.qualification_id,
                    "fingerprint": plan.fingerprint,
                    "confirmationToken": plan.confirmation_token,
                }
            )
        write_json(
            {
                "planId": "p006.7.11.15.8.1-city-parent-containment-qualification",
                "cityCount": len(rows),
                "qualifiedCount": sum(row["qualificationStatus"] == "QUALIFIED" for row in rows),
                "rejectedCount": sum(row["qualificationStatus"] == "REJECTED" for row in rows),
                "items": rows,
            },
            args.output or None,
        )
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
