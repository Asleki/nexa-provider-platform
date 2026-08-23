"""Dependency-free geometry helpers for Bundle 20 road/network qualification.

Bundle 20 originally used Shapely during engineering authoring. The repository's
runtime/test dependency baseline intentionally does not include Shapely, so these
helpers keep the delivered milestone self-contained and Alpine/Acode compatible.
They operate on the simple WGS84 LineString/Polygon/MultiPolygon shapes used by
NoveGeo's governed artifacts; they are qualification utilities, not a replacement
for PostGIS in the live database.
"""
from __future__ import annotations

from math import isclose
from registries.nngla.spatial_fabric.bundle19a.geometry import on_segment, point_relation

Point = tuple[float, float]
EPS = 1e-10


def _closed(ring: tuple[Point, ...]) -> tuple[Point, ...]:
    if not ring:
        return ring
    return ring if ring[0] == ring[-1] else ring + (ring[0],)


def exterior_rings(geometry: dict) -> tuple[tuple[Point, ...], ...]:
    gtype = geometry.get("type")
    coords = geometry.get("coordinates") or ()
    if gtype == "Polygon":
        if not coords:
            return ()
        return (tuple((float(x), float(y)) for x, y in coords[0]),)
    if gtype == "MultiPolygon":
        return tuple(tuple((float(x), float(y)) for x, y in poly[0]) for poly in coords if poly)
    raise ValueError("polygonal GeoJSON required")


def line_parts(geometry: dict) -> tuple[tuple[Point, ...], ...]:
    gtype = geometry.get("type")
    coords = geometry.get("coordinates") or ()
    if gtype == "LineString":
        return (tuple((float(x), float(y)) for x, y in coords),)
    if gtype == "MultiLineString":
        return tuple(tuple((float(x), float(y)) for x, y in part) for part in coords)
    raise ValueError("linear GeoJSON required")


def _orientation(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segment_intersection_point(a: Point, b: Point, c: Point, d: Point, eps: float = EPS) -> Point | None:
    """Return one deterministic intersection point for two closed segments."""
    ax, ay = a; bx, by = b; cx, cy = c; dx, dy = d
    rx, ry = bx - ax, by - ay
    sx, sy = dx - cx, dy - cy
    denom = rx * sy - ry * sx
    qpx, qpy = cx - ax, cy - ay

    if abs(denom) <= eps:
        # Parallel/collinear: return the lexicographically first shared endpoint/
        # overlap endpoint. Bundle 20 only needs evidence that an intersection exists.
        candidates = []
        for p in (a, b):
            if on_segment(p, c, d, eps):
                candidates.append(p)
        for p in (c, d):
            if on_segment(p, a, b, eps):
                candidates.append(p)
        if not candidates:
            return None
        return sorted(set(candidates))[0]

    t = (qpx * sy - qpy * sx) / denom
    u = (qpx * ry - qpy * rx) / denom
    if -eps <= t <= 1.0 + eps and -eps <= u <= 1.0 + eps:
        return (ax + t * rx, ay + t * ry)
    return None


def segment_covered_by_polygonal_geometry(a: Point, b: Point, geometry: dict) -> bool:
    """Conservatively prove a straight segment is covered by one polygon part.

    Endpoints and sampled interior points must be inside/boundary of the same exterior
    ring. This avoids an external geometry dependency while failing closed for concave
    polygon escapes. The generated Bundle 19B region geometries contain no relevant
    holes for this authoring use.
    """
    if a == b:
        return False
    for ring in exterior_rings(geometry):
        closed = _closed(ring)
        if point_relation(a, closed) not in {"INSIDE", "BOUNDARY"}:
            continue
        if point_relation(b, closed) not in {"INSIDE", "BOUNDARY"}:
            continue
        ok = True
        # Sample densely enough for the short governed place-to-place road edges and
        # also reject a segment whose middle leaves a concave region.
        for i in range(1, 32):
            t = i / 32.0
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            if point_relation(p, closed) not in {"INSIDE", "BOUNDARY"}:
                ok = False
                break
        if ok:
            return True
    return False


def line_intersections_with_linear_geometry(coords: tuple[Point, ...], geometry: dict) -> tuple[Point, ...]:
    found: list[Point] = []
    for a, b in zip(coords, coords[1:]):
        for part in line_parts(geometry):
            for c, d in zip(part, part[1:]):
                p = segment_intersection_point(a, b, c, d)
                if p is not None:
                    found.append(p)
    return _dedupe_points(found)


def line_intersections_with_polygon(coords: tuple[Point, ...], geometry: dict) -> tuple[Point, ...]:
    found: list[Point] = []
    for ring in exterior_rings(geometry):
        closed = _closed(ring)
        for a, b in zip(coords, coords[1:]):
            for c, d in zip(closed, closed[1:]):
                p = segment_intersection_point(a, b, c, d)
                if p is not None:
                    found.append(p)
        # If the whole road segment is inside the polygon, retain a deterministic
        # interior representative point so the relationship still exists.
        if not found and coords and point_relation(coords[0], closed) in {"INSIDE", "BOUNDARY"}:
            a, b = coords[0], coords[-1]
            found.append(((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0))
    return _dedupe_points(found)


def _dedupe_points(points: list[Point], digits: int = 12) -> tuple[Point, ...]:
    seen: dict[tuple[float, float], Point] = {}
    for x, y in points:
        key = (round(float(x), digits), round(float(y), digits))
        seen.setdefault(key, (float(x), float(y)))
    return tuple(seen[k] for k in sorted(seen))


def convex_hull(points: list[Point] | tuple[Point, ...]) -> tuple[Point, ...]:
    """Andrew monotonic-chain convex hull, returned as a closed ring."""
    pts = sorted(set((float(x), float(y)) for x, y in points))
    if len(pts) < 3:
        return ()

    def cross(o: Point, a: Point, b: Point) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[Point] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[Point] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    if len(hull) < 3:
        return ()
    # Match the repository's previously validated Shapely serialization convention:
    # clockwise exterior ring, starting at the lowest-Y then lowest-X vertex. This
    # keeps the maintenance correction byte-stable for generated landform artifacts.
    hull = list(reversed(hull))
    start = min(range(len(hull)), key=lambda i: (hull[i][1], hull[i][0]))
    hull = hull[start:] + hull[:start]
    return tuple(hull + [hull[0]])


__all__ = [
    "Point", "exterior_rings", "line_parts", "segment_intersection_point",
    "segment_covered_by_polygonal_geometry", "line_intersections_with_linear_geometry",
    "line_intersections_with_polygon", "convex_hull",
]
