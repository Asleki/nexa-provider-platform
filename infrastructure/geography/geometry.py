"""NoveGeo sovereign-boundary normalization and deterministic validation."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from typing import Any

from .contracts import GeographicCoordinate


class BoundaryValidationError(ValueError):
    """Raised when sovereign-boundary geometry violates the P004 contract."""


def _point(value: Any) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise BoundaryValidationError("each coordinate position must contain longitude and latitude")
    try:
        coordinate = GeographicCoordinate(float(value[0]), float(value[1]))
    except (TypeError, ValueError) as exc:
        raise BoundaryValidationError(str(exc)) from exc
    return coordinate.to_pair()


def _signed_area(ring: list[tuple[float, float]]) -> float:
    return sum(
        ring[index][0] * ring[index + 1][1] - ring[index + 1][0] * ring[index][1]
        for index in range(len(ring) - 1)
    ) / 2.0


def _orientation(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _segments_intersect(a, b, c, d) -> bool:
    o1, o2, o3, o4 = _orientation(a, b, c), _orientation(a, b, d), _orientation(c, d, a), _orientation(c, d, b)
    return ((o1 > 0 > o2) or (o1 < 0 < o2)) and ((o3 > 0 > o4) or (o3 < 0 < o4))


def _validate_ring(raw_ring: Any, *, exterior: bool) -> list[tuple[float, float]]:
    if not isinstance(raw_ring, list):
        raise BoundaryValidationError("polygon ring must be a list")
    ring = [_point(value) for value in raw_ring]
    if len(ring) < 4:
        raise BoundaryValidationError("polygon ring requires at least four positions")
    if ring[0] != ring[-1]:
        raise BoundaryValidationError("polygon ring must be closed")
    if len(set(ring[:-1])) < 3:
        raise BoundaryValidationError("polygon ring requires at least three distinct vertices")
    for left, right in zip(ring, ring[1:]):
        if left == right:
            raise BoundaryValidationError("consecutive duplicate vertices are forbidden")
    area = _signed_area(ring)
    if abs(area) <= 1e-12:
        raise BoundaryValidationError("polygon ring must have non-zero area")
    segments = list(zip(ring, ring[1:]))
    for index, (a, b) in enumerate(segments):
        for other_index, (c, d) in enumerate(segments):
            if other_index <= index + 1:
                continue
            if index == 0 and other_index == len(segments) - 1:
                continue
            if _segments_intersect(a, b, c, d):
                raise BoundaryValidationError("polygon ring must not self-intersect")
    should_be_ccw = exterior
    if (_signed_area(ring) > 0) != should_be_ccw:
        ring = list(reversed(ring))
    return ring


def _normalize_polygon(raw_polygon: Any) -> list[list[list[float]]]:
    if not isinstance(raw_polygon, list) or not raw_polygon:
        raise BoundaryValidationError("polygon coordinates must contain an exterior ring")
    rings = []
    for index, raw_ring in enumerate(raw_polygon):
        ring = _validate_ring(raw_ring, exterior=index == 0)
        rings.append([[longitude, latitude] for longitude, latitude in ring])
    return rings


def normalize_boundary_geometry(geometry: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(geometry, dict):
        raise BoundaryValidationError("geometry must be an object")
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geometry_type == "Polygon":
        polygons = [_normalize_polygon(coordinates)]
    elif geometry_type == "MultiPolygon":
        if not isinstance(coordinates, list) or not coordinates:
            raise BoundaryValidationError("MultiPolygon requires at least one polygon")
        polygons = [_normalize_polygon(polygon) for polygon in coordinates]
    else:
        raise BoundaryValidationError("sovereign boundary must be Polygon or MultiPolygon")
    return {"type": "MultiPolygon", "coordinates": polygons}


def validate_boundary_geometry(geometry: dict[str, Any]) -> None:
    normalize_boundary_geometry(geometry)


def iter_positions(geometry: dict[str, Any]) -> Iterable[tuple[float, float]]:
    normalized = normalize_boundary_geometry(geometry)
    for polygon in normalized["coordinates"]:
        for ring in polygon:
            for longitude, latitude in ring:
                yield float(longitude), float(latitude)


def boundary_extent(geometry: dict[str, Any]) -> tuple[float, float, float, float]:
    positions = tuple(iter_positions(geometry))
    longitudes = [position[0] for position in positions]
    latitudes = [position[1] for position in positions]
    return (min(longitudes), min(latitudes), max(longitudes), max(latitudes))


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
