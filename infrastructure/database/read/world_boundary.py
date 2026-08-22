"""Read-only PostgreSQL repository for the active published NoveGeo boundary.

P006.7.11.8 keeps the existing ``WorldBoundaryPublication`` HTTP contract while
moving live authority from filesystem v001 to qualified/published PostgreSQL v002.
The adapter performs no writes and fails closed if joined authority records disagree.
"""
from __future__ import annotations

import json
from typing import Any

from infrastructure.geography.contracts import (
    BoundaryIdentity,
    CoordinateReference,
    WorldBoundaryPublication,
)


class WorldBoundaryAuthorityError(RuntimeError):
    """Raised when PostgreSQL boundary authority records disagree."""


class PostgreSQLWorldBoundaryRepository:
    """Implements the read side of ``WorldBoundaryRepository`` using PostgreSQL."""

    _ACTIVE_PUBLIC_SQL = """
        SELECT
            p.publication_id,
            wb.boundary_id,
            wbv.boundary_version,
            wb.dataset_id,
            sp.dataset_version,
            cr.coordinate_reference_id,
            cr.version,
            cr.authority_name,
            cr.authority_code,
            cr.application_axis_order,
            cr.unit,
            ST_AsGeoJSON(wbv.geometry),
            ST_XMin(Box3D(wbv.extent)),
            ST_YMin(Box3D(wbv.extent)),
            ST_XMax(Box3D(wbv.extent)),
            ST_YMax(Box3D(wbv.extent)),
            sp.source_sha256,
            wbv.content_sha256,
            p.content_sha256,
            wbv.runtime_mode,
            p.runtime_mode,
            sp.runtime_mode,
            wbv.visibility,
            p.visibility,
            sp.visibility,
            wbv.lifecycle_status,
            p.lifecycle_status,
            q.decision,
            sp.dataset_id
        FROM geography.world_boundary wb
        JOIN geography.world_boundary_version wbv
          ON wbv.boundary_id = wb.boundary_id
        JOIN geography.source_package sp
          ON sp.source_package_id = wbv.source_package_id
        JOIN geography.coordinate_reference cr
          ON cr.coordinate_reference_id = wbv.coordinate_reference_id
         AND cr.version = wbv.coordinate_reference_version
        JOIN geography.boundary_qualification q
          ON q.boundary_id = wbv.boundary_id
         AND q.boundary_version = wbv.boundary_version
        JOIN geography.boundary_publication p
          ON p.boundary_id = wbv.boundary_id
         AND p.boundary_version = wbv.boundary_version
        WHERE wb.boundary_id = 'boundary:novegeo:sovereign'
          AND wbv.lifecycle_status = 'active'
          AND wbv.visibility = 'public'
          AND q.decision = 'qualified'
          AND p.lifecycle_status = 'active'
          AND p.visibility = 'public'
          AND cr.lifecycle_status = 'active'
        ORDER BY wbv.boundary_version DESC, p.publication_id DESC
        LIMIT 1
    """

    def __init__(self, pool: Any) -> None:
        if pool is None:
            raise TypeError("pool is required")
        self._pool = pool

    def save(self, publication: WorldBoundaryPublication) -> None:
        raise RuntimeError("PostgreSQLWorldBoundaryRepository is read-only")

    def get_active(self) -> WorldBoundaryPublication | None:
        with self._pool.connection(read_only=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._ACTIVE_PUBLIC_SQL)
                row = cursor.fetchone()
        if row is None:
            return None
        return self._publication_from_row(row)

    @staticmethod
    def _publication_from_row(row: tuple[Any, ...]) -> WorldBoundaryPublication:
        (
            publication_id,
            boundary_id,
            boundary_version,
            dataset_id,
            dataset_version,
            coordinate_reference_id,
            coordinate_reference_version,
            authority_name,
            authority_code,
            application_axis_order,
            unit,
            geometry_json,
            min_longitude,
            min_latitude,
            max_longitude,
            max_latitude,
            source_sha256,
            boundary_content_sha256,
            publication_content_sha256,
            boundary_runtime_mode,
            publication_runtime_mode,
            source_runtime_mode,
            boundary_visibility,
            publication_visibility,
            source_visibility,
            boundary_lifecycle,
            publication_lifecycle,
            qualification_decision,
            source_dataset_id,
        ) = row

        # ``world_boundary_version.content_sha256`` identifies the authoritative
        # boundary geometry/source content, while
        # ``boundary_publication.content_sha256`` identifies the publication
        # manifest.  They are intentionally different hashes in v002 and must
        # not be compared for equality.  Referential agreement is already
        # enforced by the boundary/version joins above.
        if dataset_id != source_dataset_id:
            raise WorldBoundaryAuthorityError("boundary/source dataset identity mismatch")
        if len({boundary_runtime_mode, publication_runtime_mode, source_runtime_mode}) != 1:
            raise WorldBoundaryAuthorityError("boundary runtime authority mismatch")
        if boundary_visibility != "public" or publication_visibility != "public" or source_visibility != "public":
            raise WorldBoundaryAuthorityError("boundary visibility authority mismatch")
        if boundary_lifecycle != "active" or publication_lifecycle != "active" or qualification_decision != "qualified":
            raise WorldBoundaryAuthorityError("boundary is not active, qualified and published")

        try:
            geometry = json.loads(geometry_json) if isinstance(geometry_json, str) else geometry_json
        except (TypeError, json.JSONDecodeError) as exc:
            raise WorldBoundaryAuthorityError("boundary geometry is not valid GeoJSON") from exc
        if not isinstance(geometry, dict) or geometry.get("type") != "MultiPolygon":
            raise WorldBoundaryAuthorityError("published sovereign boundary must be a MultiPolygon")

        axis_order = tuple(application_axis_order or ())
        if axis_order != ("longitude", "latitude"):
            raise WorldBoundaryAuthorityError("coordinate axis order is not longitude/latitude")

        return WorldBoundaryPublication(
            publication_id=str(publication_id),
            identity=BoundaryIdentity(str(boundary_id), int(boundary_version)),
            dataset_id=str(dataset_id),
            dataset_version=int(dataset_version),
            coordinate_reference=CoordinateReference(
                coordinate_reference_id=str(coordinate_reference_id),
                version=int(coordinate_reference_version),
                authority_name=str(authority_name),
                authority_code=str(authority_code),
                axis_order=("longitude", "latitude"),
                unit=str(unit),
            ),
            geometry=geometry,
            extent=(float(min_longitude), float(min_latitude), float(max_longitude), float(max_latitude)),
            source_sha256=str(source_sha256),
            content_sha256=str(boundary_content_sha256),
            runtime_mode=str(boundary_runtime_mode),
        )


__all__ = ["PostgreSQLWorldBoundaryRepository", "WorldBoundaryAuthorityError"]
