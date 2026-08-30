"""PostGIS evidence engine for P006.7.11.15.8.1.

The locked P006.7.11.15.8 geometry model remains unchanged: a source geometry is
reused when strictly covered; otherwise exactly one intersection with the exact
current authoritative parent REGION is performed.  This adapter only changes
how the resulting containment evidence is qualified.
"""
from __future__ import annotations

import json
from typing import Any

from registries.nngla.city_realization.postgis import PostGISCityRealizationEngine
from registries.nngla.city_realization.source import canonical_json_sha256

from .contracts import (
    ABSOLUTE_RESIDUE_MAX_M2,
    RATIO_RESIDUE_MAX,
    ContainmentEvidence,
    QualificationBasis,
    QualificationStatus,
)


class PostgreSQLCityContainmentAuthorityError(RuntimeError):
    pass


def _json_object(value: object, label: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    raise PostgreSQLCityContainmentAuthorityError(f"{label} is malformed")


class PostGISCityContainmentQualificationEngine:
    """Evaluate one CITY against the exact live parent REGION."""

    def __init__(self, connection: Any) -> None:
        if connection is None:
            raise TypeError("connection is required")
        self.connection = connection
        # Reuse only the already-locked identity/parent lookups, never its
        # post-intersection fail-fast realization predicate.
        self._locked_lookup = PostGISCityRealizationEngine(connection)

    def load_city_identity(self, city_id: str):
        return self._locked_lookup.load_city_identity(city_id)

    def load_parent_region(self, region_code: str):
        return self._locked_lookup.load_parent_region(region_code)

    def evaluate(self, source, parent) -> ContainmentEvidence:
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
                    ST_IsValid(source_geometry),
                    NOT ST_IsEmpty(source_geometry),
                    GeometryType(source_geometry),
                    source_covered,
                    ST_Area(source_geometry::geography),
                    ST_Area(
                        ST_CollectionExtract(
                            ST_Difference(source_geometry,parent_geometry),3
                        )::geography
                    ),
                    ST_IsValid(final_geometry),
                    NOT ST_IsEmpty(final_geometry),
                    GeometryType(final_geometry),
                    ST_CoveredBy(final_geometry,parent_geometry),
                    ST_Area(final_geometry::geography),
                    ST_Area(
                        ST_CollectionExtract(
                            ST_Difference(final_geometry,parent_geometry),3
                        )::geography
                    ),
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
            raise PostgreSQLCityContainmentAuthorityError(
                "exact parent REGION geometry was unavailable during containment qualification"
            )

        source_valid = bool(row[0])
        source_non_empty = bool(row[1])
        source_type = str(row[2]).upper()
        source_covered = bool(row[3])
        source_area_m2 = float(row[4] or 0.0)
        source_outside_m2 = max(0.0, float(row[5] or 0.0))
        final_valid = bool(row[6])
        final_non_empty = bool(row[7])
        final_type = str(row[8]).upper()
        final_covered = bool(row[9])
        final_area_m2 = float(row[10] or 0.0)
        final_outside_m2 = max(0.0, float(row[11] or 0.0))
        perimeter_m = float(row[12] or 0.0)
        geometry = _json_object(row[13], "realized CITY geometry")
        label_point = _json_object(row[14], "CITY label point")
        label_covered = bool(row[15])

        source_ratio = source_outside_m2 / source_area_m2 if source_area_m2 > 0 else 0.0
        final_ratio = final_outside_m2 / final_area_m2 if final_area_m2 > 0 else 0.0
        removed_m2 = max(0.0, source_area_m2 - final_area_m2)
        removed_ratio = removed_m2 / source_area_m2 if source_area_m2 > 0 else 0.0

        if (
            not source_valid
            or not source_non_empty
            or source_type not in {"POLYGON", "MULTIPOLYGON"}
            or source_type != str(source.geometry_type_code).upper()
        ):
            status = QualificationStatus.REJECTED
            basis = QualificationBasis.REJECTED_INVALID_SOURCE
        elif not final_valid or final_area_m2 <= 0.0 or perimeter_m <= 0.0:
            status = QualificationStatus.REJECTED
            basis = QualificationBasis.REJECTED_INVALID_REALIZATION
        elif not final_non_empty:
            status = QualificationStatus.REJECTED
            basis = QualificationBasis.REJECTED_EMPTY_REALIZATION
        elif final_type not in {"POLYGON", "MULTIPOLYGON"}:
            status = QualificationStatus.REJECTED
            basis = QualificationBasis.REJECTED_NON_POLYGONAL_REALIZATION
        elif not label_covered or label_point.get("type") != "Point":
            status = QualificationStatus.REJECTED
            basis = QualificationBasis.REJECTED_LABEL_POINT
        elif source_covered and final_covered:
            status = QualificationStatus.QUALIFIED
            basis = QualificationBasis.STRICT_SOURCE_COVERED
        elif final_covered:
            status = QualificationStatus.QUALIFIED
            basis = QualificationBasis.SINGLE_INTERSECTION_STRICT_COVERED
        elif final_outside_m2 == 0.0 and final_ratio == 0.0:
            status = QualificationStatus.QUALIFIED
            basis = QualificationBasis.SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE
        elif final_outside_m2 <= ABSOLUTE_RESIDUE_MAX_M2 and final_ratio <= RATIO_RESIDUE_MAX:
            status = QualificationStatus.QUALIFIED
            basis = QualificationBasis.SINGLE_INTERSECTION_NUMERICAL_RESIDUE
        else:
            status = QualificationStatus.REJECTED
            basis = QualificationBasis.REJECTED_RESIDUE_EXCEEDS_POLICY

        realization_method = (
            "SOURCE_REUSE" if source_covered else "PARENT_CONTAINED_NORMALIZATION"
        )

        return ContainmentEvidence(
            source_valid=source_valid,
            source_non_empty=source_non_empty,
            source_geometry_type=source_type,
            source_strict_covered=source_covered,
            source_area_m2=source_area_m2,
            source_outside_parent_m2=source_outside_m2,
            source_outside_parent_ratio=source_ratio,
            normalized_valid=final_valid,
            normalized_non_empty=final_non_empty,
            normalized_geometry_type=final_type,
            normalized_strict_covered=final_covered,
            normalized_area_m2=final_area_m2,
            normalized_outside_parent_m2=final_outside_m2,
            normalized_outside_parent_ratio=final_ratio,
            perimeter_m=perimeter_m,
            label_point_covered=label_covered,
            geometry=geometry,
            label_point=label_point,
            geometry_sha256=canonical_json_sha256(geometry),
            realization_method=realization_method,
            area_removed_m2=removed_m2,
            area_removed_ratio=removed_ratio,
            qualification_status=status,
            qualification_basis=basis,
        )
