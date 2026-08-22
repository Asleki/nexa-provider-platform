"""Read-only PostgreSQL access for live NNGLA status and public projections."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PUBLIC_FAMILIES = (
    "PLACE",
    "ADMINISTRATIVE_AREA",
    "GEOGRAPHIC_FEATURE",
    "ROAD",
    "ADDRESS",
    "PARCEL",
)

SOURCE_DATASETS = {
    "PLACE": ("dataset:novegeo:places:v001:700", "1"),
    "ADMINISTRATIVE_AREA": ("dataset:novegeo:administrative-areas:v001:192", "1"),
    "GEOGRAPHIC_FEATURE": ("dataset:novegeo:geographic-features:v001:21", "1"),
    "ROAD": ("dataset:novegeo:roads:v001:900", "1"),
}

COORDINATE_DATASET = ("dataset:novegeo:spatial-fabric:coordinate-candidates", "2")


@dataclass(frozen=True, slots=True)
class NNGLAFamilyCounts:
    source_count: int
    canonical_count: int
    published_count: int
    map_renderable_count: int

    def __post_init__(self) -> None:
        values = (self.source_count, self.canonical_count, self.published_count, self.map_renderable_count)
        if any(value < 0 for value in values):
            raise ValueError("NNGLA family counts cannot be negative")
        if self.canonical_count > self.source_count:
            raise ValueError("canonical count cannot exceed governed source count")
        if self.published_count > self.canonical_count:
            raise ValueError("published count cannot exceed canonical count")
        if self.map_renderable_count > self.published_count:
            raise ValueError("map-renderable count cannot exceed published count")


class NNGLAReadAuthorityError(RuntimeError):
    """Raised when live PostgreSQL read authority cannot be reconciled safely."""


class PostgreSQLNNGLAReadRepository:
    """Read-only repository for canonical counts and explicit public projections."""

    _SOURCE_COUNTS_SQL = """
        SELECT d.dataset_id, d.dataset_version, SUM(a.row_count)::bigint
        FROM geography.nngla_source_dataset d
        JOIN geography.nngla_source_artifact a
          ON a.dataset_id = d.dataset_id
         AND a.dataset_version = d.dataset_version
        WHERE (d.dataset_id, d.dataset_version) IN (
            (%s, %s), (%s, %s), (%s, %s), (%s, %s)
        )
        GROUP BY d.dataset_id, d.dataset_version
    """

    _CANONICAL_COUNTS_SQL = """
        SELECT 'PLACE', COUNT(*)::bigint FROM geography.nngla_place_reference
        UNION ALL
        SELECT 'ADMINISTRATIVE_AREA', COUNT(*)::bigint FROM geography.nngla_administrative_area
        UNION ALL
        SELECT 'GEOGRAPHIC_FEATURE', COUNT(*)::bigint
          FROM geography.nngla_canonical_crosswalk
         WHERE dataset_id = %s AND dataset_version = %s
        UNION ALL
        SELECT 'ROAD', COUNT(*)::bigint FROM geography.nngla_road
        UNION ALL
        SELECT 'ADDRESS', COUNT(*)::bigint FROM geography.nngla_address
        UNION ALL
        SELECT 'PARCEL', COUNT(*)::bigint FROM geography.nngla_parcel
    """

    _PROJECTION_COUNTS_SQL = """
        SELECT record_family,
               COUNT(*)::bigint AS published_count,
               COUNT(*) FILTER (WHERE geometry_id IS NOT NULL)::bigint AS map_renderable_count
        FROM geography.nngla_spatial_read_projection_v1
        WHERE runtime_mode = %s AND visibility = 'PUBLIC'
        GROUP BY record_family
    """

    _PROJECTION_VERSION_SQL = """
        SELECT COALESCE(MAX(read_model_version), 1)
        FROM geography.nngla_spatial_read_projection_v1
        WHERE runtime_mode = %s
    """

    _PUBLIC_ITEMS_SQL = """
        SELECT subject_id, record_family, display_name, runtime_mode,
               publication_reference, geometry_id, geometry_version,
               read_model_version, projected_at
        FROM geography.nngla_spatial_read_projection_v1
        WHERE runtime_mode = %s
          AND visibility = 'PUBLIC'
          AND record_family = %s
        ORDER BY subject_id
    """

    _COORDINATE_MIGRATION_SQL = """
        SELECT
            (SELECT COUNT(*)::bigint
               FROM geography.nngla_canonical_crosswalk
              WHERE dataset_id = %s AND dataset_version = %s),
            (SELECT SUM(a.row_count)::bigint
               FROM geography.nngla_source_artifact a
              WHERE a.dataset_id = %s AND a.dataset_version = %s)
    """

    def __init__(self, pool: Any, *, runtime_mode: str = "simulation") -> None:
        if pool is None:
            raise TypeError("pool is required")
        normalized = str(runtime_mode).strip().lower()
        if normalized not in {"simulation", "production"}:
            raise ValueError("NNGLA read runtime must be simulation or production")
        self._pool = pool
        self.runtime_mode = normalized

    @staticmethod
    def _fetchall(connection: Any, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())

    @staticmethod
    def _fetchone(connection: Any, sql: str, params: tuple[Any, ...] = ()) -> tuple[Any, ...] | None:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def family_counts(self) -> dict[str, NNGLAFamilyCounts]:
        source_params: list[str] = []
        for family in ("PLACE", "ADMINISTRATIVE_AREA", "GEOGRAPHIC_FEATURE", "ROAD"):
            source_params.extend(SOURCE_DATASETS[family])
        feature_dataset = SOURCE_DATASETS["GEOGRAPHIC_FEATURE"]

        with self._pool.connection(read_only=True) as connection:
            source_rows = self._fetchall(connection, self._SOURCE_COUNTS_SQL, tuple(source_params))
            canonical_rows = self._fetchall(connection, self._CANONICAL_COUNTS_SQL, feature_dataset)
            projection_rows = self._fetchall(connection, self._PROJECTION_COUNTS_SQL, (self.runtime_mode,))

        source_by_dataset = {(str(dataset_id), str(version)): row_count for dataset_id, version, row_count in source_rows}
        source_counts: dict[str, int] = {"ADDRESS": 0, "PARCEL": 0}
        for family, dataset_key in SOURCE_DATASETS.items():
            row_count = source_by_dataset.get(dataset_key)
            if row_count is None:
                raise NNGLAReadAuthorityError(f"governed source row count is unavailable for {family}")
            source_counts[family] = int(row_count)

        canonical_counts = {str(family): int(count) for family, count in canonical_rows}
        missing = set(PUBLIC_FAMILIES) - set(canonical_counts)
        if missing:
            raise NNGLAReadAuthorityError(f"canonical count query omitted families: {sorted(missing)}")

        projection_counts = {str(family): (int(published), int(map_count)) for family, published, map_count in projection_rows}
        result: dict[str, NNGLAFamilyCounts] = {}
        for family in PUBLIC_FAMILIES:
            published, map_count = projection_counts.get(family, (0, 0))
            result[family] = NNGLAFamilyCounts(
                source_count=source_counts[family],
                canonical_count=canonical_counts[family],
                published_count=published,
                map_renderable_count=map_count,
            )
        return result

    def read_model_version(self) -> int:
        with self._pool.connection(read_only=True) as connection:
            row = self._fetchone(connection, self._PROJECTION_VERSION_SQL, (self.runtime_mode,))
        return int(row[0]) if row else 1

    def coordinate_migration_status(self) -> str:
        dataset_id, dataset_version = COORDINATE_DATASET
        params = (dataset_id, dataset_version, dataset_id, dataset_version)
        with self._pool.connection(read_only=True) as connection:
            row = self._fetchone(connection, self._COORDINATE_MIGRATION_SQL, params)
        if row is None:
            raise NNGLAReadAuthorityError("coordinate migration truth is unavailable")
        canonical_count, source_count = row
        if source_count is None or int(source_count) <= 0:
            raise NNGLAReadAuthorityError("coordinate source row count is unavailable")
        return "EXECUTED" if int(canonical_count) == int(source_count) else "INCOMPLETE"

    def public_items(self, family: str) -> tuple[dict[str, object], ...]:
        normalized = str(family).strip().upper()
        if normalized not in PUBLIC_FAMILIES:
            raise KeyError(f"unsupported public NNGLA family: {family}")
        with self._pool.connection(read_only=True) as connection:
            rows = self._fetchall(connection, self._PUBLIC_ITEMS_SQL, (self.runtime_mode, normalized))
        items = []
        for (
            subject_id,
            record_family,
            display_name,
            runtime_mode,
            publication_reference,
            geometry_id,
            geometry_version,
            read_model_version,
            _projected_at,
        ) in rows:
            items.append({
                "subjectId": str(subject_id),
                "family": str(record_family),
                "displayName": str(display_name),
                "lifecycleStatus": "PUBLIC_PROJECTED",
                "publicEligible": True,
                "mapRenderable": geometry_id is not None,
                "geometryReference": str(geometry_id) if geometry_id is not None else None,
                "runtimeEffectScope": "RUNTIME_SCOPED",
                "visibilityReasons": ["PUBLIC_PROJECTION"],
                "attributes": {
                    "publicationReference": str(publication_reference),
                    "runtimeMode": str(runtime_mode),
                    "geometryVersion": int(geometry_version) if geometry_version is not None else None,
                },
                "publicationReference": str(publication_reference),
                "runtimeMode": str(runtime_mode),
                "geometryVersion": int(geometry_version) if geometry_version is not None else None,
                "readModelVersion": int(read_model_version),
            })
        return tuple(items)


__all__ = [
    "COORDINATE_DATASET",
    "NNGLAFamilyCounts",
    "NNGLAReadAuthorityError",
    "PostgreSQLNNGLAReadRepository",
    "PUBLIC_FAMILIES",
    "SOURCE_DATASETS",
]
