#!/usr/bin/env python3
"""Verify committed CITY publication through the locked .15.7 public-map adapter."""
from __future__ import annotations

import argparse
from contextlib import contextmanager

from infrastructure.database.read.nngla_city_public_map import PostgreSQLCityPublicMapRepository
from infrastructure.database.read.nngla_national_map import MapBounds

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
    value.add_argument("--runtime-mode", default="simulation", choices=("simulation", "production"))
    return value


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    connection = connect_postgresql()
    try:
        with connection.transaction():
            connection.execute("SET TRANSACTION READ ONLY")
            repo = PostgreSQLCityPublicMapRepository(
                _ConnectionPoolAdapter(connection),
                runtime_mode=args.runtime_mode,
            )
            item = repo.get_subject(args.city)
            if item is None:
                raise RuntimeError(f"CITY is not exposed by locked .15.7 public-map adapter: {args.city}")
            metadata = repo.metadata_for_subjects([args.city]).get(args.city)
            if metadata is None:
                raise RuntimeError("CITY map metadata is unavailable")
            payload = {
                "status": "VERIFIED",
                "cityId": item.subject_id,
                "displayName": item.display_name,
                "family": item.family,
                "classificationCode": item.classification_code,
                "geometryId": item.geometry_id,
                "geometryType": item.geometry_type,
                "publicationReference": item.publication_reference,
                "parentRegionId": metadata.parent_region_id,
                "areaM2": metadata.area_m2,
                "perimeterM": metadata.perimeter_m,
                "labelPoint": metadata.label_point,
                "readRuntime": args.runtime_mode,
                "sourceView": metadata.source_view,
            }
        write_json(payload)
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
