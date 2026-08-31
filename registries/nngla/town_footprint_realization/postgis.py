"""Read-only live identity/parent authority and PostGIS validation for TOWN footprints."""
from __future__ import annotations

import json
from typing import Any

from .contracts import RealizedTownFootprint, TownIdentity, TownSourceEvidence
from .planning import canonical_sha256


class TownAuthorityError(RuntimeError):
    pass


def _json_object(value: object, label: str) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
    raise TownAuthorityError(f"{label} is malformed")


class PostGISTownFootprintEngine:
    def __init__(self, connection: Any) -> None:
        if connection is None:
            raise TypeError("connection is required")
        self.connection = connection

    def load_identity(self, place_id: str) -> TownIdentity:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.place_id,n.canonical_name,p.region_code,p.source_place_code,
                       p.parent_source_place_code,parent.place_id,parent.place_type_code,
                       admin.administrative_area_id,m.municipality_geometry_id,m.geometry_sha256
                FROM geography.nngla_place_reference p
                JOIN geography.nngla_geographic_name n
                  ON n.name_id=p.settlement_name_record_id
                JOIN geography.nngla_place_reference parent
                  ON parent.source_place_code=p.parent_source_place_code
                JOIN geography.nngla_administrative_area admin
                  ON admin.source_record_id=parent.source_place_code
                 AND admin.administrative_type_code='MUNICIPALITY'
                JOIN geography.nngla_municipality_public_read_v1 m
                  ON m.municipality_id=admin.administrative_area_id
                 AND m.publication_status='PUBLISHED'
                 AND m.qualification_status='QUALIFIED'
                WHERE p.place_id=%s
                  AND upper(p.place_type_code)='TOWN'
                  AND upper(parent.place_type_code)='MUNICIPALITY'
                """,
                (place_id,),
            )
            rows = list(cursor.fetchall())
        if len(rows) != 1:
            raise TownAuthorityError(f"exactly one governed TOWN/parent MUNICIPALITY authority is required: {place_id}")
        row = rows[0]
        return TownIdentity(*(str(value) for value in row))

    def realize(self, source: TownSourceEvidence, identity: TownIdentity) -> RealizedTownFootprint:
        geojson = json.dumps(source.geometry, separators=(",", ":"), ensure_ascii=False)
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                WITH parent AS (
                  SELECT geometry
                  FROM geography.nngla_municipality_public_read_v1
                  WHERE municipality_id=%s
                    AND municipality_geometry_id=%s
                    AND geometry_sha256=%s
                    AND publication_status='PUBLISHED'
                    AND qualification_status='QUALIFIED'
                ), src AS (
                  SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s),4326) AS geometry
                )
                SELECT ST_IsValid(src.geometry),NOT ST_IsEmpty(src.geometry),ST_GeometryType(src.geometry),
                       ST_CoveredBy(src.geometry,parent.geometry),
                       ST_Area(src.geometry::geography),ST_Perimeter(src.geometry::geography),
                       ST_AsGeoJSON(src.geometry,15)::jsonb,
                       ST_AsGeoJSON(ST_PointOnSurface(src.geometry),15)::jsonb,
                       ST_CoveredBy(ST_PointOnSurface(src.geometry),src.geometry)
                FROM src CROSS JOIN parent
                """,
                (
                    identity.parent_administrative_area_id,
                    identity.parent_municipality_geometry_id,
                    identity.parent_municipality_geometry_sha256,
                    geojson,
                ),
            )
            row = cursor.fetchone()
        if row is None:
            raise TownAuthorityError("current parent MUNICIPALITY geometry is unavailable")
        geometry_type = str(row[2]).removeprefix("ST_").upper()
        if not bool(row[0]) or not bool(row[1]) or geometry_type != "POLYGON":
            raise TownAuthorityError("TOWN settlement footprint is invalid, empty or no longer Polygon")
        if not bool(row[3]):
            raise TownAuthorityError("TOWN settlement footprint is not covered by its published parent MUNICIPALITY")
        geometry = _json_object(row[6], "TOWN settlement footprint")
        label_point = _json_object(row[7], "TOWN label point")
        if label_point.get("type") != "Point" or not bool(row[8]):
            raise TownAuthorityError("TOWN label point is invalid")
        area_m2 = float(row[4])
        perimeter_m = float(row[5])
        if area_m2 <= 0 or perimeter_m <= 0:
            raise TownAuthorityError("TOWN measurements must be positive")
        return RealizedTownFootprint(
            place_id=source.place_id,
            geometry_type_code=geometry_type,
            geometry=geometry,
            geometry_sha256=canonical_sha256(geometry),
            label_point=label_point,
            area_m2=area_m2,
            area_km2=area_m2 / 1_000_000.0,
            perimeter_m=perimeter_m,
            perimeter_km=perimeter_m / 1000.0,
            covered_by_parent_municipality=True,
        )


def validate_geojson(connection, geojson_text):
    """Compatibility helper retained for the initial focused tests."""
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT ST_IsValid(g),NOT ST_IsEmpty(g),ST_GeometryType(g) IN ('ST_Polygon','ST_MultiPolygon')
               FROM (SELECT ST_SetSRID(ST_GeomFromGeoJSON(%s),4326) g) s""",
            (geojson_text,),
        )
        row = cursor.fetchone()
    return tuple(bool(value) for value in row)
