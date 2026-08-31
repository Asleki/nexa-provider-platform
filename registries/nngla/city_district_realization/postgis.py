"""Read-only PostGIS realization and exact partition proof for CITY_DISTRICT."""
from __future__ import annotations

import json
from typing import Any

from .contracts import (
    CityDistrictIdentity,
    CityDistrictSourceEvidence,
    ParentCityAuthority,
    RealizedCityDistrict,
)
from .planning import canonical_sha256


class CityDistrictAuthorityError(RuntimeError):
    pass


def _json_object(value: object, label: str) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    raise CityDistrictAuthorityError(f"{label} is malformed")


class PostGISCityDistrictEngine:
    def __init__(self, connection: Any) -> None:
        if connection is None:
            raise TypeError("connection is required")
        self.connection = connection

    def load_city(self, city_id: str) -> ParentCityAuthority:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT city_id,canonical_name,region_code,source_record_id,
                       city_geometry_id,geometry_sha256
                FROM geography.nngla_city_public_read_v1
                WHERE city_id=%s
                  AND administrative_type_code='CITY'
                  AND qualification_status='QUALIFIED'
                  AND publication_status='PUBLISHED'
                """,
                (str(city_id).strip(),),
            )
            rows = list(cursor.fetchall())
        if len(rows) != 1:
            raise CityDistrictAuthorityError("exactly one published CITY authority is required")
        row = rows[0]
        return ParentCityAuthority(
            city_id=str(row[0]),
            canonical_name=str(row[1]),
            region_code=str(row[2]),
            source_record_id=str(row[3]),
            city_geometry_id=str(row[4]),
            geometry_sha256=str(row[5]),
        )

    def load_identity(self, district_id: str) -> CityDistrictIdentity:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT administrative_area_id,canonical_name,region_code,
                       source_record_id,parent_source_record_id
                FROM geography.nngla_administrative_area
                WHERE administrative_area_id=%s
                  AND administrative_type_code='CITY_DISTRICT'
                """,
                (district_id,),
            )
            rows = list(cursor.fetchall())
        if len(rows) != 1:
            raise CityDistrictAuthorityError(
                f"exactly one CITY_DISTRICT identity is required: {district_id}"
            )
        row = rows[0]
        return CityDistrictIdentity(*(str(value) for value in row))

    def realize(
        self,
        source: CityDistrictSourceEvidence,
        city: ParentCityAuthority,
    ) -> RealizedCityDistrict:
        geojson = json.dumps(source.geometry, separators=(",", ":"), ensure_ascii=False)
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                WITH city AS (
                  SELECT geometry
                  FROM geography.nngla_city_geometry_record
                  WHERE city_geometry_id=%s
                    AND administrative_area_id=%s
                    AND geometry_sha256=%s
                    AND effective_to IS NULL
                    AND qualification_status='QUALIFIED'
                ), src AS (
                  SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s),4326) AS geometry
                )
                SELECT
                  ST_IsValid(src.geometry),
                  NOT ST_IsEmpty(src.geometry),
                  ST_GeometryType(src.geometry),
                  ST_CoveredBy(src.geometry,city.geometry),
                  ST_Area(src.geometry::geography),
                  ST_Perimeter(src.geometry::geography),
                  ST_AsGeoJSON(src.geometry,15)::jsonb,
                  ST_AsGeoJSON(ST_PointOnSurface(src.geometry),15)::jsonb,
                  ST_CoveredBy(ST_PointOnSurface(src.geometry),src.geometry)
                FROM src CROSS JOIN city
                """,
                (
                    city.city_geometry_id,
                    city.city_id,
                    city.geometry_sha256,
                    geojson,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise CityDistrictAuthorityError("exact current CITY geometry is unavailable")
        geometry_type = str(row[2]).removeprefix("ST_").upper()
        if not bool(row[0]) or not bool(row[1]) or geometry_type not in {"POLYGON", "MULTIPOLYGON"}:
            raise CityDistrictAuthorityError("CITY_DISTRICT geometry is invalid, empty or non-polygonal")
        if not bool(row[3]):
            raise CityDistrictAuthorityError("CITY_DISTRICT geometry is not covered by current CITY")
        geometry = _json_object(row[6], "CITY_DISTRICT geometry")
        label_point = _json_object(row[7], "CITY_DISTRICT label point")
        if label_point.get("type") != "Point" or not bool(row[8]):
            raise CityDistrictAuthorityError("CITY_DISTRICT label point is invalid")
        area_m2 = float(row[4])
        perimeter_m = float(row[5])
        if area_m2 <= 0 or perimeter_m <= 0:
            raise CityDistrictAuthorityError("CITY_DISTRICT measurements must be positive")
        return RealizedCityDistrict(
            district_id=source.administrative_area_id,
            realization_method="SOURCE_REUSE",
            geometry_type_code=geometry_type,
            geometry=geometry,
            geometry_sha256=canonical_sha256(geometry),
            label_point=label_point,
            area_m2=area_m2,
            area_km2=area_m2 / 1_000_000.0,
            perimeter_m=perimeter_m,
            perimeter_km=perimeter_m / 1000.0,
        )

    def qualify_partition(
        self,
        city: ParentCityAuthority,
        districts: tuple[RealizedCityDistrict, ...],
    ) -> dict[str, object]:
        if len(districts) != 8:
            raise CityDistrictAuthorityError("exactly eight CITY_DISTRICT geometries are required")
        payload = json.dumps(
            [item.geometry for item in districts],
            separators=(",", ":"),
            ensure_ascii=False,
        )
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                WITH city AS (
                  SELECT geometry
                  FROM geography.nngla_city_geometry_record
                  WHERE city_geometry_id=%s
                    AND administrative_area_id=%s
                    AND geometry_sha256=%s
                    AND effective_to IS NULL
                    AND qualification_status='QUALIFIED'
                ), src AS (
                  SELECT row_number() OVER () AS ordinal,
                         ST_SetSRID(ST_GeomFromGeoJSON(value::text),4326) AS geometry
                  FROM jsonb_array_elements(%s::jsonb)
                ), aggregate AS (
                  SELECT count(*)::integer AS observed_count,
                         bool_and(ST_IsValid(geometry)) AS all_valid,
                         bool_and(NOT ST_IsEmpty(geometry)) AS all_non_empty,
                         bool_and(ST_GeometryType(geometry) IN ('ST_Polygon','ST_MultiPolygon')) AS all_polygonal,
                         bool_and(ST_CoveredBy(geometry,city.geometry)) AS all_covered_by_city,
                         ST_UnaryUnion(ST_Collect(geometry)) AS district_union
                  FROM src CROSS JOIN city
                ), overlap AS (
                  SELECT COALESCE(sum(
                    ST_Area(ST_CollectionExtract(ST_Intersection(a.geometry,b.geometry),3)::geography)
                  ),0.0) AS sibling_overlap_m2
                  FROM src a
                  JOIN src b ON a.ordinal < b.ordinal
                )
                SELECT aggregate.observed_count,aggregate.all_valid,aggregate.all_non_empty,
                       aggregate.all_polygonal,aggregate.all_covered_by_city,
                       overlap.sibling_overlap_m2,
                       ST_Equals(aggregate.district_union,city.geometry),
                       ST_Area(aggregate.district_union::geography),
                       ST_Area(city.geometry::geography),
                       ST_Area(ST_CollectionExtract(
                         ST_SymDifference(aggregate.district_union,city.geometry),3
                       )::geography)
                FROM aggregate CROSS JOIN overlap CROSS JOIN city
                """,
                (
                    city.city_geometry_id,
                    city.city_id,
                    city.geometry_sha256,
                    payload,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise CityDistrictAuthorityError("CITY_DISTRICT exact partition proof is unavailable")
        result = {
            "expected_count": 8,
            "observed_count": int(row[0]),
            "all_valid": bool(row[1]),
            "all_non_empty": bool(row[2]),
            "all_polygonal": bool(row[3]),
            "all_covered_by_city": bool(row[4]),
            "sibling_positive_overlap_m2": max(0.0, float(row[5])),
            "union_equals_city": bool(row[6]),
            "union_area_m2": float(row[7]),
            "city_area_m2": float(row[8]),
            "symmetric_difference_m2": max(0.0, float(row[9])),
        }
        result["partition_status"] = "COMPLETE" if (
            result["observed_count"] == result["expected_count"]
            and result["all_valid"]
            and result["all_non_empty"]
            and result["all_polygonal"]
            and result["all_covered_by_city"]
            and result["sibling_positive_overlap_m2"] == 0.0
            and result["union_equals_city"]
        ) else "INCOMPLETE"
        return result
