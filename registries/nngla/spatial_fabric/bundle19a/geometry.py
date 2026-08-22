"""Dependency-free geometry helpers for deterministic settlement siting qualification."""
from __future__ import annotations

from math import asin, atan2, cos, degrees, radians, sin, sqrt

EARTH_RADIUS_M = 6_371_008.8
KM_PER_DEGREE_LAT = 111.32


def haversine_m(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    p1, p2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(p1) * cos(p2) * sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_M * asin(min(1.0, sqrt(a)))


def offset_coordinate(longitude: float, latitude: float, distance_km: float, bearing_degrees: float) -> tuple[float, float]:
    """Spherical forward-geodesic offset, adequate for deterministic national siting."""
    angular = distance_km * 1000.0 / EARTH_RADIUS_M
    bearing = radians(bearing_degrees)
    lat1 = radians(latitude)
    lon1 = radians(longitude)
    lat2 = asin(sin(lat1) * cos(angular) + cos(lat1) * sin(angular) * cos(bearing))
    lon2 = lon1 + atan2(
        sin(bearing) * sin(angular) * cos(lat1),
        cos(angular) - sin(lat1) * sin(lat2),
    )
    lon = (degrees(lon2) + 540.0) % 360.0 - 180.0
    return round(lon, 6), round(degrees(lat2), 6)


def on_segment(point: tuple[float, float], a: tuple[float, float], b: tuple[float, float], eps: float = 1e-10) -> bool:
    x, y = point
    x1, y1 = a
    x2, y2 = b
    cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
    if abs(cross) > eps:
        return False
    return min(x1, x2) - eps <= x <= max(x1, x2) + eps and min(y1, y2) - eps <= y <= max(y1, y2) + eps


def point_relation(point: tuple[float, float], ring: tuple[tuple[float, float], ...]) -> str:
    if len(ring) < 4:
        return "OUTSIDE"
    pts = ring if ring[0] == ring[-1] else ring + (ring[0],)
    x, y = point
    inside = False
    for a, b in zip(pts, pts[1:]):
        if on_segment(point, a, b):
            return "BOUNDARY"
        x1, y1 = a
        x2, y2 = b
        if (y1 > y) != (y2 > y):
            x_intersection = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if abs(x_intersection - x) <= 1e-12:
                return "BOUNDARY"
            if x_intersection > x:
                inside = not inside
    return "INSIDE" if inside else "OUTSIDE"


def containing_polygon(point: tuple[float, float], polygons: tuple[dict[str, object], ...]) -> dict[str, object] | None:
    x, y = point
    for polygon in polygons:
        if not (polygon["min_lon"] <= x <= polygon["max_lon"] and polygon["min_lat"] <= y <= polygon["max_lat"]):
            continue
        if point_relation(point, polygon["ring"]) in {"INSIDE", "BOUNDARY"}:
            return polygon
    return None


def segment_intersects(a1, a2, b1, b2, eps: float = 1e-10) -> bool:
    def orient(p, q, r):
        value = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        if abs(value) <= eps:
            return 0
        return 1 if value > 0 else 2

    o1, o2, o3, o4 = orient(a1, a2, b1), orient(a1, a2, b2), orient(b1, b2, a1), orient(b1, b2, a2)
    if o1 != o2 and o3 != o4:
        return True
    return (
        (o1 == 0 and on_segment(b1, a1, a2, eps))
        or (o2 == 0 and on_segment(b2, a1, a2, eps))
        or (o3 == 0 and on_segment(a1, b1, b2, eps))
        or (o4 == 0 and on_segment(a2, b1, b2, eps))
    )


def polygons_intersect(ring_a: tuple[tuple[float, float], ...], ring_b: tuple[tuple[float, float], ...]) -> bool:
    a = ring_a if ring_a[0] == ring_a[-1] else ring_a + (ring_a[0],)
    b = ring_b if ring_b[0] == ring_b[-1] else ring_b + (ring_b[0],)
    for a1, a2 in zip(a, a[1:]):
        for b1, b2 in zip(b, b[1:]):
            if segment_intersects(a1, a2, b1, b2):
                return True
    if point_relation(a[0], b) in {"INSIDE", "BOUNDARY"}:
        return True
    if point_relation(b[0], a) in {"INSIDE", "BOUNDARY"}:
        return True
    return False


def regular_ring(longitude: float, latitude: float, radius_km: float, vertices: int = 24) -> tuple[tuple[float, float], ...]:
    if vertices < 8:
        raise ValueError("settlement footprint requires at least eight perimeter vertices")
    points = tuple(offset_coordinate(longitude, latitude, radius_km, (360.0 * index) / vertices) for index in range(vertices))
    return points + (points[0],)


def ring_is_within(ring: tuple[tuple[float, float], ...], polygon_ring: tuple[tuple[float, float], ...]) -> bool:
    """Return True only when an entire candidate ring is strictly inside a simple polygon.

    Vertex-only or sparse edge sampling is unsafe for a concave sovereign boundary: an
    edge can briefly leave the polygon between sampled points and re-enter before the
    next sample.  Bundle 19A therefore requires every candidate vertex to be in the
    polygon interior *and* rejects any candidate edge that touches or crosses the
    polygon boundary.  Footprint generation can then shrink a coastal candidate until
    it is unambiguously land-contained.
    """
    inner = ring if ring[0] == ring[-1] else ring + (ring[0],)
    outer = polygon_ring if polygon_ring[0] == polygon_ring[-1] else polygon_ring + (polygon_ring[0],)

    if any(point_relation(point, outer) != "INSIDE" for point in inner[:-1]):
        return False

    for a1, a2 in zip(inner, inner[1:]):
        for b1, b2 in zip(outer, outer[1:]):
            if segment_intersects(a1, a2, b1, b2):
                return False
    return True


def polygon_area_sq_km(ring: tuple[tuple[float, float], ...]) -> float:
    """Approximate local planar area for evidence/reporting, not legal area measurement."""
    if len(ring) < 4:
        return 0.0
    avg_lat = sum(lat for _, lat in ring[:-1]) / max(1, len(ring) - 1)
    scale_x = KM_PER_DEGREE_LAT * cos(radians(avg_lat))
    scale_y = KM_PER_DEGREE_LAT
    area = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        area += (x1 * scale_x) * (y2 * scale_y) - (x2 * scale_x) * (y1 * scale_y)
    return abs(area) / 2.0


def ring_self_intersects(ring: tuple[tuple[float, float], ...]) -> bool:
    pts = ring if ring[0] == ring[-1] else ring + (ring[0],)
    segments = list(zip(pts, pts[1:]))
    for i, (a1, a2) in enumerate(segments):
        for j, (b1, b2) in enumerate(segments):
            if j <= i + 1:
                continue
            if i == 0 and j == len(segments) - 1:
                continue
            if segment_intersects(a1, a2, b1, b2):
                return True
    return False


__all__ = [
    "EARTH_RADIUS_M", "haversine_m", "offset_coordinate", "on_segment", "point_relation",
    "containing_polygon", "segment_intersects", "polygons_intersect", "regular_ring",
    "ring_is_within", "polygon_area_sq_km", "ring_self_intersects",
]
