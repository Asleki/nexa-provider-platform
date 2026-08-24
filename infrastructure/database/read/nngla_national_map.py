"""P006.7.11.15.2 read-only PostgreSQL map projection over PUBLIC NNGLA geography."""
from __future__ import annotations
from dataclasses import dataclass
import json
from typing import Any, Iterable

MAP_FAMILIES = ("PLACE", "ADMINISTRATIVE_AREA", "ROAD", "GEOGRAPHIC_FEATURE")

class NNGLAMapReadAuthorityError(RuntimeError):
    pass

@dataclass(frozen=True, slots=True)
class MapBounds:
    min_longitude: float
    min_latitude: float
    max_longitude: float
    max_latitude: float
    def __post_init__(self) -> None:
        if not (-180 <= self.min_longitude < self.max_longitude <= 180):
            raise ValueError("invalid longitude bounds")
        if not (-90 <= self.min_latitude < self.max_latitude <= 90):
            raise ValueError("invalid latitude bounds")

@dataclass(frozen=True, slots=True)
class NationalMapFeature:
    subject_id: str
    family: str
    display_name: str
    publication_reference: str
    geometry_id: str
    geometry_version: int
    geometry_role: str
    geometry_type: str
    crs_code: str
    geometry: dict[str, object]
    runtime_effect_scope: str
    classification_scheme: str | None
    classification_code: str | None
    read_model_version: int

@dataclass(frozen=True, slots=True)
class NationalMapPage:
    items: tuple[NationalMapFeature, ...]
    has_more: bool
    last_key: tuple[str, str] | None
    read_model_version: int

class PostgreSQLNNGLANationalMapRepository:
    """Read only the existing governed PUBLIC read projection.

    Migration-18's nngla_spatial_read_projection_v1 is the public contract.
    Bundle 22B does not require, install, or write the later Bundle-21 durable
    publication ledger.  PUBLIC projection rows still require a non-null
    publication_reference and qualified current geometry.
    """
    def __init__(self, pool: Any, *, runtime_mode: str = "simulation") -> None:
        if pool is None:
            raise TypeError("pool is required")
        normalized = str(runtime_mode).strip().lower()
        if normalized not in {"simulation", "production"}:
            raise ValueError("runtime_mode must be simulation or production")
        self.pool = pool
        self.runtime_mode = normalized

    @staticmethod
    def _geometry(value: object) -> dict[str, object]:
        if isinstance(value, dict): return value
        if isinstance(value, str):
            parsed = json.loads(value)
            if isinstance(parsed, dict): return parsed
        raise NNGLAMapReadAuthorityError("PostGIS geometry payload is malformed")

    def _query(self, *, bounds: MapBounds | None, families: Iterable[str], limit: int, after: tuple[str, str] | None, subject_id: str | None = None) -> NationalMapPage:
        selected = tuple(dict.fromkeys(str(f).strip().upper() for f in families))
        if not selected or any(f not in MAP_FAMILIES for f in selected):
            raise ValueError("at least one supported map family is required")
        if not 1 <= int(limit) <= 2000:
            raise ValueError("limit must be between 1 and 2000")
        family_placeholders = ",".join(["%s"] * len(selected))
        where = [
            "p.runtime_mode=%s",
            "p.publication_reference IS NOT NULL",
            f"p.record_family IN ({family_placeholders})",
            "p.geometry_id IS NOT NULL",
        ]
        params: list[object] = [self.runtime_mode, *selected]
        if subject_id is not None:
            where.append("p.subject_id=%s"); params.append(subject_id)
        if after is not None:
            where.append("(p.record_family,p.subject_id)>(%s,%s)"); params.extend(after)
        if bounds is not None:
            where.append("ST_Intersects(g.geometry,ST_MakeEnvelope(%s,%s,%s,%s,4326))")
            params.extend([bounds.min_longitude,bounds.min_latitude,bounds.max_longitude,bounds.max_latitude])
        sql = f"""
            WITH current_projection AS (
              SELECT DISTINCT ON (subject_id,runtime_mode)
                     subject_id,record_family,display_name,runtime_mode,publication_reference,
                     geometry_id,geometry_version,read_model_version
              FROM geography.nngla_spatial_read_projection_v1
              WHERE visibility='PUBLIC' AND runtime_mode=%s
              ORDER BY subject_id,runtime_mode,read_model_version DESC
            )
            SELECT p.subject_id,p.record_family,p.display_name,p.publication_reference,
                   p.geometry_id,p.geometry_version,g.geometry_role_code,g.geometry_type_code,g.crs_code,
                   ST_AsGeoJSON(g.geometry,8)::jsonb,
                   COALESCE(a.runtime_effect_scope,'RUNTIME_SCOPED'),
                   CASE p.record_family
                     WHEN 'PLACE' THEN 'NNGLA_PLACE_TYPE'
                     WHEN 'ADMINISTRATIVE_AREA' THEN 'NNGLA_ADMIN_TYPE'
                     WHEN 'ROAD' THEN 'NNGLA_ROAD_CLASS'
                     WHEN 'GEOGRAPHIC_FEATURE' THEN 'NNGLA_FEATURE_TYPE'
                   END,
                   CASE p.record_family
                     WHEN 'PLACE' THEN (SELECT place_type_code FROM geography.nngla_place_reference x WHERE x.place_id=p.subject_id)
                     WHEN 'ADMINISTRATIVE_AREA' THEN (SELECT administrative_type_code FROM geography.nngla_administrative_area x WHERE x.administrative_area_id=p.subject_id)
                     WHEN 'ROAD' THEN (SELECT road_class_code FROM geography.nngla_road x WHERE x.road_id=p.subject_id)
                     WHEN 'GEOGRAPHIC_FEATURE' THEN (SELECT feature_type_code FROM geography.nngla_name_assignment x WHERE x.subject_id=p.subject_id AND x.effective_to IS NULL ORDER BY x.assignment_id LIMIT 1)
                   END,
                   p.read_model_version
            FROM current_projection p
            JOIN geography.nngla_geometry_version g ON g.geometry_id=p.geometry_id AND g.valid_to IS NULL
            JOIN geography.nngla_geometry_authority_record a ON a.geometry_id=g.geometry_id AND a.valid_to IS NULL
            WHERE {' AND '.join(where)}
              AND a.qualification_status='QUALIFIED'
              AND (g.runtime_mode=p.runtime_mode OR a.runtime_effect_scope='SHARED_REFERENCE')
            ORDER BY p.record_family,p.subject_id
            LIMIT %s
        """
        query_params = [self.runtime_mode, *params, int(limit) + 1]
        with self.pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, tuple(query_params))
                rows = list(cursor.fetchall())
        has_more = len(rows) > limit
        rows = rows[:limit]
        items = []
        for row in rows:
            items.append(NationalMapFeature(
                subject_id=str(row[0]), family=str(row[1]), display_name=str(row[2]),
                publication_reference=str(row[3]), geometry_id=str(row[4]), geometry_version=int(row[5]),
                geometry_role=str(row[6]), geometry_type=str(row[7]), crs_code=str(row[8]),
                geometry=self._geometry(row[9]), runtime_effect_scope=str(row[10]),
                classification_scheme=str(row[11]) if row[11] is not None else None,
                classification_code=str(row[12]) if row[12] is not None else None,
                read_model_version=int(row[13]),
            ))
        last_key = (items[-1].family, items[-1].subject_id) if has_more and items else None
        read_model_version = max((item.read_model_version for item in items), default=1)
        return NationalMapPage(tuple(items), has_more, last_key, read_model_version)

    def list_features(self, *, bounds: MapBounds, families: Iterable[str] = MAP_FAMILIES, limit: int = 500, after: tuple[str, str] | None = None) -> NationalMapPage:
        return self._query(bounds=bounds, families=families, limit=limit, after=after)

    def get_subject(self, subject_id: str) -> NationalMapFeature | None:
        page = self._query(bounds=None, families=MAP_FAMILIES, limit=1, after=None, subject_id=str(subject_id))
        return page.items[0] if page.items else None

__all__ = ["MAP_FAMILIES","MapBounds","NationalMapFeature","NationalMapPage","NNGLAMapReadAuthorityError","PostgreSQLNNGLANationalMapRepository"]
