"""PostGIS authority/realization adapter for P006.7.11.15.8.

There is one and only one geometry transformation in the normalization path:
intersection with the exact current authoritative parent REGION.  No iterative
repair, grid snapping, shared-face reconstruction or historical Delivery 1-3
CITY workflow is invoked.
"""
from __future__ import annotations

import json
from typing import Any

from .contracts import (
    CityIdentity,
    CitySourceEvidence,
    ParentRegionAuthority,
    RealizationMethod,
    RealizedGeometry,
)
from .source import canonical_json_sha256


class PostgreSQLCityRealizationAuthorityError(RuntimeError):
    pass


def _json_object(value: object, label: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    raise PostgreSQLCityRealizationAuthorityError(f"{label} is malformed")


class PostGISCityRealizationEngine:
    def __init__(self, connection: Any) -> None:
        if connection is None:
            raise TypeError("connection is required")
        self.connection = connection

    def load_city_identity(self, city_id: str) -> CityIdentity:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT administrative_area_id, canonical_name, region_code
                FROM geography.nngla_administrative_area
                WHERE administrative_area_id=%s
                  AND administrative_type_code='CITY'
                """,
                (city_id,),
            )
            rows = list(cursor.fetchall())
        if len(rows) != 1:
            raise PostgreSQLCityRealizationAuthorityError(
                f"exactly one CITY identity is required: {city_id}"
            )
        row = rows[0]
        return CityIdentity(str(row[0]), str(row[1]), str(row[2]))

    def load_parent_region(self, region_code: str) -> ParentRegionAuthority:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT region_id, canonical_name, region_code,
                       region_geometry_id, geometry_sha256
                FROM geography.nngla_region_public_read_v1
                WHERE region_code=%s
                  AND administrative_type_code='REGION'
                  AND qualification_status='QUALIFIED'
                  AND publication_status='PUBLISHED'
                """,
                (region_code,),
            )
            rows = list(cursor.fetchall())
        if len(rows) != 1:
            raise PostgreSQLCityRealizationAuthorityError(
                f"exactly one published authoritative REGION is required for region_code={region_code}"
            )
        row = rows[0]
        return ParentRegionAuthority(
            region_id=str(row[0]),
            canonical_name=str(row[1]),
            region_code=str(row[2]),
            region_geometry_id=str(row[3]),
            geometry_sha256=str(row[4]),
        )

    def realize(
        self,
        source: CitySourceEvidence,
        parent: ParentRegionAuthority,
    ) -> RealizedGeometry:
        source_geojson = json.dumps(source.geometry, separators=(",", ":"), ensure_ascii=False)
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                WITH parent AS (
                    SELECT geometry
                    FROM geography.nngla_region_geometry_record
                    WHERE region_geometry_id=%s
                      AND administrative_area_id=%s
                      AND geometry_sha256=%s
                      AND effective_to IS NULL
                      AND qualification_status='QUALIFIED'
                ),
                source AS (
                    SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s),4326) AS geometry
                ),
                candidate AS (
                    SELECT
                        source.geometry AS source_geometry,
                        parent.geometry AS parent_geometry,
                        ST_CoveredBy(source.geometry,parent.geometry) AS source_covered,
                        CASE
                            WHEN ST_CoveredBy(source.geometry,parent.geometry)
                                THEN source.geometry
                            ELSE ST_CollectionExtract(
                                ST_Intersection(source.geometry,parent.geometry),
                                3
                            )
                        END AS final_geometry
                    FROM source CROSS JOIN parent
                )
                SELECT
                    source_covered,
                    ST_IsValid(source_geometry),
                    NOT ST_IsEmpty(source_geometry),
                    GeometryType(source_geometry),
                    ST_IsValid(final_geometry),
                    NOT ST_IsEmpty(final_geometry),
                    GeometryType(final_geometry),
                    ST_CoveredBy(final_geometry,parent_geometry),
                    ST_Area(source_geometry::geography),
                    ST_Area(ST_CollectionExtract(ST_Difference(source_geometry,parent_geometry),3)::geography),
                    ST_Area(final_geometry::geography),
                    ST_Perimeter(final_geometry::geography),
                    ST_AsGeoJSON(final_geometry,15)::jsonb,
                    ST_AsGeoJSON(ST_PointOnSurface(final_geometry),15)::jsonb,
                    ST_CoveredBy(ST_PointOnSurface(final_geometry),final_geometry)
                FROM candidate
                """,
                (
                    parent.region_geometry_id,
                    parent.region_id,
                    parent.geometry_sha256,
                    source_geojson,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise PostgreSQLCityRealizationAuthorityError(
                "exact parent REGION geometry was unavailable during realization"
            )
        source_covered = bool(row[0])
        if not bool(row[1]) or not bool(row[2]):
            raise PostgreSQLCityRealizationAuthorityError("CITY source geometry is invalid or empty")
        source_type = str(row[3]).upper()
        if source_type not in {"POLYGON", "MULTIPOLYGON"}:
            raise PostgreSQLCityRealizationAuthorityError("CITY source geometry is not polygonal")
        if source_type != source.geometry_type_code:
            raise PostgreSQLCityRealizationAuthorityError("CITY source geometry type metadata changed")
        if not bool(row[4]) or not bool(row[5]):
            raise PostgreSQLCityRealizationAuthorityError("realized CITY geometry is invalid or empty")
        final_type = str(row[6]).upper()
        if final_type not in {"POLYGON", "MULTIPOLYGON"}:
            raise PostgreSQLCityRealizationAuthorityError("realized CITY geometry is not polygonal")
        if not bool(row[7]):
            raise PostgreSQLCityRealizationAuthorityError("realized CITY geometry is outside parent REGION")
        source_area_m2 = float(row[8])
        outside_m2 = max(0.0, float(row[9]))
        final_area_m2 = float(row[10])
        perimeter_m = float(row[11])
        if source_area_m2 <= 0 or final_area_m2 <= 0 or perimeter_m <= 0:
            raise PostgreSQLCityRealizationAuthorityError("CITY geometry measurements must be positive")
        geometry = _json_object(row[12], "realized CITY geometry")
        label_point = _json_object(row[13], "CITY label point")
        if label_point.get("type") != "Point" or not bool(row[14]):
            raise PostgreSQLCityRealizationAuthorityError("CITY label point is not covered by final geometry")
        removed_m2 = max(0.0, source_area_m2 - final_area_m2)
        method = (
            RealizationMethod.SOURCE_REUSE
            if source_covered
            else RealizationMethod.PARENT_CONTAINED_NORMALIZATION
        )
        return RealizedGeometry(
            method=method,
            geometry_type_code=final_type,
            geometry=geometry,
            geometry_sha256=canonical_json_sha256(geometry),
            label_point=label_point,
            source_area_m2=source_area_m2,
            source_outside_parent_m2=outside_m2,
            source_outside_parent_ratio=outside_m2 / source_area_m2,
            final_area_m2=final_area_m2,
            final_area_km2=final_area_m2 / 1_000_000.0,
            final_perimeter_m=perimeter_m,
            final_perimeter_km=perimeter_m / 1_000.0,
            area_removed_m2=removed_m2,
            area_removed_ratio=removed_m2 / source_area_m2,
        )
