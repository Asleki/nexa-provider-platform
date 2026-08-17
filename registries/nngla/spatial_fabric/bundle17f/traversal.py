"""Bundle 17F free-form geometry construction and source traversal qualification."""
from __future__ import annotations
from functools import lru_cache
from math import isfinite

from ._shared import GEOMETRY_PATH, ROOT, csv_rows, file_sha256
from .contracts import GeometryTraversalQualification

SUPPORTED_GEOMETRY_TYPES = frozenset({"POINT", "LINESTRING", "POLYGON", "MULTIPOINT", "MULTILINESTRING", "MULTIPOLYGON"})


def _point(value) -> tuple[float, float]:
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError("coordinate must be a longitude/latitude pair")
    lon, lat = float(value[0]), float(value[1])
    if not (isfinite(lon) and isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90):
        raise ValueError("coordinate outside WGS84 numeric bounds")
    return lon, lat


def construct_free_form_geometry(geometry_type: str, coordinates):
    """Validate ordinary geometry coordinates without grid or identifier-sequence restrictions."""
    kind = str(geometry_type).upper()
    if kind == "POINT":
        return {"type": kind, "coordinates": _point(coordinates)}
    if kind == "LINESTRING":
        pts = tuple(_point(p) for p in coordinates)
        if len(pts) < 2 or len(set(pts)) < 2:
            raise ValueError("LINESTRING requires at least two distinct points")
        return {"type": kind, "coordinates": pts}
    if kind == "POLYGON":
        rings = []
        for ring in coordinates:
            pts = tuple(_point(p) for p in ring)
            if len(pts) < 4 or pts[0] != pts[-1] or len(set(pts[:-1])) < 3:
                raise ValueError("POLYGON ring must be closed and contain at least three distinct vertices")
            rings.append(pts)
        if not rings:
            raise ValueError("POLYGON requires at least one ring")
        return {"type": kind, "coordinates": tuple(rings)}
    raise ValueError("construction helper supports POINT, LINESTRING and POLYGON; multi-geometries remain valid source types")


def segment_vectors(geometry: dict) -> tuple[tuple[float, float], ...]:
    kind = geometry["type"]
    if kind == "POINT":
        return ()
    points = geometry["coordinates"] if kind == "LINESTRING" else geometry["coordinates"][0]
    return tuple((b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))


def has_arbitrary_direction_segment(geometry: dict) -> bool:
    return any(dx != 0 and dy != 0 for dx, dy in segment_vectors(geometry))


@lru_cache(maxsize=1)
def derive_geometry_traversal_qualifications() -> tuple[GeometryTraversalQualification, ...]:
    out = []
    for index, row in enumerate(csv_rows(GEOMETRY_PATH), start=1):
        source_path = ROOT / row["source_path_reference"]
        exists = source_path.is_file()
        digest_matches = bool(exists and file_sha256(source_path) == row["checksum_sha256"])
        type_ok = row["geometry_type_code"] in SUPPORTED_GEOMETRY_TYPES
        crs_ok = row["crs_code"] == "NG-CRS-EPSG4326"
        source_ok = row["qualification_status"] == "QUALIFIED"
        checks = (exists, digest_matches, type_ok, crs_ok, source_ok)
        status = "PASS" if all(checks) else "FAIL"
        findings = "" if status == "PASS" else "SOURCE_OR_GEOMETRY_METADATA_PRECONDITION_FAILED"
        out.append(GeometryTraversalQualification(
            traversal_qualification_id=f"NG-GTRAV-{index:06d}",
            geometry_id=row["geometry_version_candidate_id"], subject_type=row["subject_type"], subject_id=row["subject_id"],
            geometry_type_code=row["geometry_type_code"], crs_code=row["crs_code"], source_path_reference=row["source_path_reference"],
            source_artifact_exists=exists, source_sha256_matches=digest_matches, geometry_type_supported=type_ok,
            crs_valid=crs_ok, qualified_source=source_ok,
            traversal_basis="COORDINATE_SEQUENCE_GEOMETRY_NOT_IDENTIFIER_TOPOLOGY",
            identifier_sequence_used=False, traversal_status=status, findings=findings,
        ))
    return tuple(out)


__all__ = [
    "SUPPORTED_GEOMETRY_TYPES", "construct_free_form_geometry", "segment_vectors", "has_arbitrary_direction_segment",
    "derive_geometry_traversal_qualifications",
]
