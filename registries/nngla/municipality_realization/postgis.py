"""Read-only PostGIS realization and exact partition proof for MUNICIPALITY."""
from __future__ import annotations

import json
from typing import Any

from .contracts import (
    MunicipalityIdentity,
    MunicipalitySourceEvidence,
    ParentCityAuthority,
    ParentRegionAuthority,
    PartitionEvidence,
    RealizationMethod,
    RealizedMunicipality,
)
from .planning import canonical_sha256


class MunicipalityAuthorityError(RuntimeError):
    pass


def _json_object(value: object, label: str) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    raise MunicipalityAuthorityError(f"{label} is malformed")


class PostGISMunicipalityEngine:
    def __init__(self, connection: Any) -> None:
        if connection is None:
            raise TypeError("connection is required")
        self.connection = connection

    def load_region(self, region_id: str) -> ParentRegionAuthority:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT region_id,canonical_name,region_code,source_record_id,
                       region_geometry_id,geometry_sha256
                FROM geography.nngla_region_public_read_v1
                WHERE region_id=%s
                  AND administrative_type_code='REGION'
                  AND qualification_status='QUALIFIED'
                  AND publication_status='PUBLISHED'
                """,
                (region_id,),
            )
            rows = list(cursor.fetchall())
        if len(rows) != 1:
            raise MunicipalityAuthorityError("exactly one published REGION authority is required")
        row = rows[0]
        return ParentRegionAuthority(
            region_id=str(row[0]),
            canonical_name=str(row[1]),
            region_code=str(row[2]),
            source_record_id=str(row[3]),
            region_geometry_id=str(row[4]),
            geometry_sha256=str(row[5]),
        )

    def load_city(self, region_id: str) -> ParentCityAuthority:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT city_id,city_geometry_id,geometry_sha256,publication_id
                FROM geography.nngla_city_public_read_v1
                WHERE parent_region_id=%s
                  AND administrative_type_code='CITY'
                  AND qualification_status='QUALIFIED'
                  AND publication_status='PUBLISHED'
                ORDER BY city_id
                """,
                (region_id,),
            )
            rows = list(cursor.fetchall())
        if len(rows) != 1:
            raise MunicipalityAuthorityError("exactly one published CITY is required per REGION")
        row = rows[0]
        return ParentCityAuthority(
            city_id=str(row[0]),
            city_geometry_id=str(row[1]),
            geometry_sha256=str(row[2]),
            publication_id=str(row[3]),
        )

    def load_identity(self, municipality_id: str) -> MunicipalityIdentity:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT administrative_area_id,canonical_name,region_code,
                       source_record_id,parent_source_record_id
                FROM geography.nngla_administrative_area
                WHERE administrative_area_id=%s
                  AND administrative_type_code='MUNICIPALITY'
                """,
                (municipality_id,),
            )
            rows = list(cursor.fetchall())
        if len(rows) != 1:
            raise MunicipalityAuthorityError(
                f"exactly one MUNICIPALITY identity is required: {municipality_id}"
            )
        row = rows[0]
        return MunicipalityIdentity(
            administrative_area_id=str(row[0]),
            canonical_name=str(row[1]),
            region_code=str(row[2]),
            source_record_id=str(row[3]),
            parent_source_record_id=str(row[4]),
        )

    def realize(
        self,
        source: MunicipalitySourceEvidence,
        region: ParentRegionAuthority,
        city: ParentCityAuthority,
    ) -> RealizedMunicipality:
        geojson = json.dumps(source.geometry, separators=(",", ":"), ensure_ascii=False)
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                WITH region AS (
                  SELECT geometry
                  FROM geography.nngla_region_geometry_record
                  WHERE region_geometry_id=%s
                    AND administrative_area_id=%s
                    AND geometry_sha256=%s
                    AND effective_to IS NULL
                    AND qualification_status='QUALIFIED'
                ),
                city AS (
                  SELECT geometry
                  FROM geography.nngla_city_geometry_record
                  WHERE city_geometry_id=%s
                    AND administrative_area_id=%s
                    AND geometry_sha256=%s
                    AND effective_to IS NULL
                    AND qualification_status='QUALIFIED'
                ),
                source AS (
                  SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s),4326) AS geometry
                ),
                calc AS (
                  SELECT
                    source.geometry AS source_geometry,
                    region.geometry AS region_geometry,
                    city.geometry AS city_geometry,
                    ST_CoveredBy(source.geometry,region.geometry) AS source_covered,
                    ST_Area(
                      ST_CollectionExtract(
                        ST_Intersection(source.geometry,city.geometry),3
                      )::geography
                    ) AS source_city_overlap_m2,
                    ST_Area(
                      ST_CollectionExtract(
                        ST_Difference(source.geometry,region.geometry),3
                      )::geography
                    ) AS source_outside_region_m2,
                    CASE
                      WHEN ST_CoveredBy(source.geometry,region.geometry)
                       AND ST_Area(
                         ST_CollectionExtract(
                           ST_Intersection(source.geometry,city.geometry),3
                         )::geography
                       )=0
                      THEN source.geometry
                      ELSE ST_CollectionExtract(
                        ST_Difference(
                          ST_CollectionExtract(
                            ST_Intersection(source.geometry,region.geometry),3
                          ),
                          city.geometry
                        ),3
                      )
                    END AS final_geometry
                  FROM source CROSS JOIN region CROSS JOIN city
                )
                SELECT
                  ST_IsValid(source_geometry),
                  NOT ST_IsEmpty(source_geometry),
                  GeometryType(source_geometry),
                  ST_IsValid(final_geometry),
                  NOT ST_IsEmpty(final_geometry),
                  GeometryType(final_geometry),
                  ST_CoveredBy(final_geometry,region_geometry),
                  ST_Area(
                    ST_CollectionExtract(
                      ST_Intersection(final_geometry,city_geometry),3
                    )::geography
                  ) AS final_city_overlap_m2,
                  ST_Area(source_geometry::geography),
                  source_outside_region_m2,
                  source_city_overlap_m2,
                  ST_Area(final_geometry::geography),
                  ST_Perimeter(final_geometry::geography),
                  ST_AsGeoJSON(final_geometry,15)::jsonb,
                  ST_AsGeoJSON(ST_PointOnSurface(final_geometry),15)::jsonb,
                  ST_CoveredBy(ST_PointOnSurface(final_geometry),final_geometry),
                  source_covered
                FROM calc
                """,
                (
                    region.region_geometry_id,
                    region.region_id,
                    region.geometry_sha256,
                    city.city_geometry_id,
                    city.city_id,
                    city.geometry_sha256,
                    geojson,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise MunicipalityAuthorityError("exact current REGION/CITY fabric is unavailable")
        if not bool(row[0]) or not bool(row[1]) or str(row[2]).upper() not in {"POLYGON", "MULTIPOLYGON"}:
            raise MunicipalityAuthorityError("MUNICIPALITY source is invalid, empty or non-polygonal")
        if not bool(row[3]) or not bool(row[4]) or str(row[5]).upper() not in {"POLYGON", "MULTIPOLYGON"}:
            raise MunicipalityAuthorityError("realized MUNICIPALITY is invalid, empty or non-polygonal")
        if not bool(row[6]):
            raise MunicipalityAuthorityError("realized MUNICIPALITY is not covered by current REGION")
        if float(row[7]) != 0:
            raise MunicipalityAuthorityError("realized MUNICIPALITY has positive-area CITY overlap")
        geometry = _json_object(row[13], "MUNICIPALITY geometry")
        label_point = _json_object(row[14], "MUNICIPALITY label point")
        if label_point.get("type") != "Point" or not bool(row[15]):
            raise MunicipalityAuthorityError("MUNICIPALITY label point is invalid")
        area_m2 = float(row[11])
        perimeter_m = float(row[12])
        if area_m2 <= 0 or perimeter_m <= 0:
            raise MunicipalityAuthorityError("MUNICIPALITY measurements must be positive")
        source_covered = bool(row[16])
        source_city_overlap = max(0.0, float(row[10]))
        method = (
            RealizationMethod.SOURCE_REUSE.value
            if source_covered and source_city_overlap == 0
            else RealizationMethod.REGION_CITY_CONTAINED_NORMALIZATION.value
        )
        return RealizedMunicipality(
            municipality_id=source.administrative_area_id,
            realization_method=method,
            geometry_type_code=str(row[5]).upper(),
            geometry=geometry,
            geometry_sha256=canonical_sha256(geometry),
            label_point=label_point,
            source_area_m2=float(row[8]),
            source_outside_region_m2=max(0.0, float(row[9])),
            source_city_overlap_m2=source_city_overlap,
            area_m2=area_m2,
            area_km2=area_m2 / 1_000_000.0,
            perimeter_m=perimeter_m,
            perimeter_km=perimeter_m / 1000.0,
        )

    def qualify_partition(
        self,
        region: ParentRegionAuthority,
        city: ParentCityAuthority,
        municipalities: tuple[RealizedMunicipality, ...],
    ) -> PartitionEvidence:
        if len(municipalities) != 3:
            raise MunicipalityAuthorityError("exactly three MUNICIPALITY geometries are required")
        geoms = [
            json.dumps(item.geometry, separators=(",", ":"), ensure_ascii=False)
            for item in municipalities
        ]
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                WITH region AS (
                  SELECT geometry
                  FROM geography.nngla_region_geometry_record
                  WHERE region_geometry_id=%s
                    AND administrative_area_id=%s
                    AND geometry_sha256=%s
                    AND effective_to IS NULL
                    AND qualification_status='QUALIFIED'
                ),
                city AS (
                  SELECT geometry
                  FROM geography.nngla_city_geometry_record
                  WHERE city_geometry_id=%s
                    AND administrative_area_id=%s
                    AND geometry_sha256=%s
                    AND effective_to IS NULL
                    AND qualification_status='QUALIFIED'
                ),
                m AS (
                  SELECT
                    ST_SetSRID(ST_GeomFromGeoJSON(%s),4326) AS m1,
                    ST_SetSRID(ST_GeomFromGeoJSON(%s),4326) AS m2,
                    ST_SetSRID(ST_GeomFromGeoJSON(%s),4326) AS m3
                ),
                proof AS (
                  SELECT
                    region.geometry AS r,
                    city.geometry AS c,
                    m1,m2,m3,
                    ST_UnaryUnion(
                      ST_Collect(ARRAY[city.geometry,m1,m2,m3])
                    ) AS u
                  FROM region CROSS JOIN city CROSS JOIN m
                )
                SELECT
                  ST_IsValid(m1) AND ST_IsValid(m2) AND ST_IsValid(m3),
                  NOT ST_IsEmpty(m1) AND NOT ST_IsEmpty(m2) AND NOT ST_IsEmpty(m3),
                  GeometryType(m1) IN ('POLYGON','MULTIPOLYGON')
                    AND GeometryType(m2) IN ('POLYGON','MULTIPOLYGON')
                    AND GeometryType(m3) IN ('POLYGON','MULTIPOLYGON'),
                  ST_CoveredBy(m1,r) AND ST_CoveredBy(m2,r) AND ST_CoveredBy(m3,r),
                  ST_CoveredBy(c,r),
                  ST_Area(ST_CollectionExtract(ST_Intersection(m1,m2),3)::geography)
                    + ST_Area(ST_CollectionExtract(ST_Intersection(m1,m3),3)::geography)
                    + ST_Area(ST_CollectionExtract(ST_Intersection(m2,m3),3)::geography),
                  ST_Area(ST_CollectionExtract(ST_Intersection(c,m1),3)::geography)
                    + ST_Area(ST_CollectionExtract(ST_Intersection(c,m2),3)::geography)
                    + ST_Area(ST_CollectionExtract(ST_Intersection(c,m3),3)::geography),
                  ST_Equals(u,r),
                  ST_Area(u::geography),
                  ST_Area(r::geography),
                  ST_Area(ST_CollectionExtract(ST_SymDifference(u,r),3)::geography)
                FROM proof
                """,
                (
                    region.region_geometry_id,
                    region.region_id,
                    region.geometry_sha256,
                    city.city_geometry_id,
                    city.city_id,
                    city.geometry_sha256,
                    *geoms,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise MunicipalityAuthorityError("MUNICIPALITY partition proof is unavailable")
        all_valid = bool(row[0])
        all_non_empty = bool(row[1])
        all_polygonal = bool(row[2])
        all_covered = bool(row[3])
        city_covered = bool(row[4])
        sibling_overlap = max(0.0, float(row[5]))
        city_overlap = max(0.0, float(row[6]))
        equals = bool(row[7])
        complete = (
            all_valid
            and all_non_empty
            and all_polygonal
            and all_covered
            and city_covered
            and sibling_overlap == 0
            and city_overlap == 0
            and equals
        )
        return PartitionEvidence(
            all_valid=all_valid,
            all_non_empty=all_non_empty,
            all_polygonal=all_polygonal,
            all_covered_by_region=all_covered,
            city_covered_by_region=city_covered,
            municipality_sibling_positive_overlap_m2=sibling_overlap,
            city_municipality_positive_overlap_m2=city_overlap,
            union_equals_region=equals,
            union_area_m2=float(row[8]),
            region_area_m2=float(row[9]),
            symmetric_difference_m2=max(0.0, float(row[10])),
            partition_status="COMPLETE" if complete else "INCOMPLETE",
        )
