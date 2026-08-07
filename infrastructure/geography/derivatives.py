"""P004.M1.4 deterministic public-safe sovereign-boundary derivatives."""
from __future__ import annotations

import json
from dataclasses import dataclass
from math import hypot
from pathlib import Path
from typing import Any

from .geometry import boundary_extent, canonical_sha256, normalize_boundary_geometry
from .refinement import BoundaryRefinementError, SovereignQualificationReceipt, qualify_v002_boundary


@dataclass(frozen=True, slots=True)
class BoundaryDerivativeSpecification:
    derivative_id: str
    resolution_class: str
    algorithm_id: str
    algorithm_version: int
    tolerance_degrees: float
    coordinate_precision: int = 6


STANDARD_DERIVATIVE = BoundaryDerivativeSpecification(
    derivative_id="derivative:novegeo:sovereign:v002:standard:v001",
    resolution_class="standard",
    algorithm_id="simplification:novegeo:closed-ring-rdp:v001",
    algorithm_version=1,
    tolerance_degrees=0.005,
)

OVERVIEW_DERIVATIVE = BoundaryDerivativeSpecification(
    derivative_id="derivative:novegeo:sovereign:v002:overview:v001",
    resolution_class="overview",
    algorithm_id="simplification:novegeo:closed-ring-rdp:v001",
    algorithm_version=1,
    tolerance_degrees=0.02,
)

PUBLIC_DERIVATIVE_SPECS = (STANDARD_DERIVATIVE, OVERVIEW_DERIVATIVE)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BoundaryRefinementError(message)


def _load_candidate(root: Path) -> dict[str, Any]:
    path = root / "candidate/novegeo_world_boundary_v002.geojson"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BoundaryRefinementError(f"cannot read v002 candidate: {exc}") from exc
    _require(isinstance(value, dict), "v002 candidate must be a JSON object")
    return value


def _perpendicular_distance(point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]) -> float:
    x, y = point
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    if dx == 0.0 and dy == 0.0:
        return hypot(x - x1, y - y1)
    scale = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
    projection = (x1 + scale * dx, y1 + scale * dy)
    return hypot(x - projection[0], y - projection[1])


def _rdp(points: list[tuple[float, float]], tolerance: float) -> list[tuple[float, float]]:
    if len(points) <= 2:
        return list(points)
    start, end = points[0], points[-1]
    max_distance = -1.0
    max_index = -1
    for index, point in enumerate(points[1:-1], start=1):
        distance = _perpendicular_distance(point, start, end)
        if distance > max_distance:
            max_distance = distance
            max_index = index
    if max_distance > tolerance:
        left = _rdp(points[: max_index + 1], tolerance)
        right = _rdp(points[max_index:], tolerance)
        return left[:-1] + right
    return [start, end]


def _simplify_closed_ring(raw_ring: list[list[float]], specification: BoundaryDerivativeSpecification) -> list[list[float]]:
    _require(len(raw_ring) >= 4 and raw_ring[0] == raw_ring[-1], "source ring must be closed before simplification")
    points = [(float(value[0]), float(value[1])) for value in raw_ring[:-1]]
    _require(len(points) >= 3, "source ring requires at least three unique vertices")

    anchor_index = min(range(len(points)), key=lambda index: (points[index][0], points[index][1], index))
    anchor = points[anchor_index]
    opposite_index = max(
        range(len(points)),
        key=lambda index: ((points[index][0] - anchor[0]) ** 2 + (points[index][1] - anchor[1]) ** 2, -index),
    )
    _require(opposite_index != anchor_index, "closed ring requires a distinct opposite anchor")

    if anchor_index < opposite_index:
        first_path = points[anchor_index : opposite_index + 1]
        second_path = points[opposite_index:] + points[: anchor_index + 1]
    else:
        first_path = points[anchor_index:] + points[: opposite_index + 1]
        second_path = points[opposite_index : anchor_index + 1]

    first = _rdp(first_path, specification.tolerance_degrees)
    second = _rdp(second_path, specification.tolerance_degrees)
    simplified = first[:-1] + second[:-1]
    _require(len(simplified) >= 3, "simplification may not collapse a boundary ring")
    rounded = [[round(longitude, specification.coordinate_precision), round(latitude, specification.coordinate_precision)] for longitude, latitude in simplified]
    rounded.append(list(rounded[0]))
    return rounded


def _simplify_geometry(geometry: dict[str, Any], specification: BoundaryDerivativeSpecification) -> dict[str, Any]:
    source = normalize_boundary_geometry(geometry)
    coordinates: list[list[list[list[float]]]] = []
    for polygon in source["coordinates"]:
        simplified_polygon = [_simplify_closed_ring(ring, specification) for ring in polygon]
        coordinates.append(simplified_polygon)
    return normalize_boundary_geometry({"type": "MultiPolygon", "coordinates": coordinates})


def _vertex_count(geometry: dict[str, Any]) -> int:
    normalized = normalize_boundary_geometry(geometry)
    return sum(len(ring) - 1 for polygon in normalized["coordinates"] for ring in polygon)


def build_public_boundary_derivative(
    world_boundary_root: Path,
    specification: BoundaryDerivativeSpecification,
    qualification: SovereignQualificationReceipt | None = None,
) -> dict[str, Any]:
    root = Path(world_boundary_root)
    qualification = qualification or qualify_v002_boundary(root)
    _require(qualification.decision == "qualified", "public derivatives require a qualified v002 source")
    candidate = _load_candidate(root)
    feature = candidate["features"][0]
    source_geometry = normalize_boundary_geometry(feature["geometry"])
    derivative_geometry = _simplify_geometry(source_geometry, specification)

    source_vertex_count = _vertex_count(source_geometry)
    derivative_vertex_count = _vertex_count(derivative_geometry)
    _require(derivative_vertex_count < source_vertex_count, "public derivative must reduce boundary vertex count")
    _require(len(derivative_geometry["coordinates"]) == qualification.polygon_count, "public derivative must preserve polygon count")
    _require(len(derivative_geometry["coordinates"]) - 1 == qualification.offshore_island_count, "public derivative must preserve offshore islands")

    source_extent = qualification.extent
    derived_extent = boundary_extent(derivative_geometry)
    maximum_extent_shift = max(abs(source_extent[index] - derived_extent[index]) for index in range(4))
    _require(maximum_extent_shift <= 0.05, "public derivative materially changes the national extent")
    _require(derived_extent[1] < 0.0 < derived_extent[3], "public derivative must preserve equator crossing")

    properties = {
        "derivativeId": specification.derivative_id,
        "derivativeVersion": 1,
        "resolutionClass": specification.resolution_class,
        "sourceBoundaryId": qualification.boundary_id,
        "sourceBoundaryVersion": qualification.boundary_version,
        "sourceQualificationId": qualification.qualification_id,
        "sourceQualificationReceiptSha256": qualification.receipt_sha256,
        "datasetId": qualification.dataset_id,
        "datasetVersion": qualification.dataset_version,
        "coordinateReferenceId": qualification.coordinate_reference_id,
        "coordinateReferenceVersion": qualification.coordinate_reference_version,
        "runtimeMode": qualification.runtime_mode,
        "visibility": "public",
        "lifecycleStatus": "derivative_candidate",
        "simplificationAlgorithmId": specification.algorithm_id,
        "simplificationAlgorithmVersion": specification.algorithm_version,
        "simplificationToleranceDegrees": specification.tolerance_degrees,
        "coordinatePrecisionDecimalPlaces": specification.coordinate_precision,
        "sourceVertexCount": source_vertex_count,
        "derivativeVertexCount": derivative_vertex_count,
        "polygonCount": qualification.polygon_count,
        "offshoreIslandCount": qualification.offshore_island_count,
        "sourceGeometrySha256": qualification.normalized_geometry_sha256,
        "derivativeGeometrySha256": canonical_sha256(derivative_geometry),
        "extent": {
            "minLongitude": derived_extent[0],
            "minLatitude": derived_extent[1],
            "maxLongitude": derived_extent[2],
            "maxLatitude": derived_extent[3],
        },
        "runtimePublicationDeferredTo": "P004.M1.5",
    }
    document = {
        "type": "FeatureCollection",
        "novegeoDerivativeContract": "public-boundary-derivative:novegeo:v001",
        "features": [{"type": "Feature", "properties": properties, "geometry": derivative_geometry}],
    }
    properties["contentSha256"] = canonical_sha256({
        "derivativeId": specification.derivative_id,
        "sourceQualificationReceiptSha256": qualification.receipt_sha256,
        "geometry": derivative_geometry,
    })
    return document


def validate_public_boundary_derivative(document: dict[str, Any], qualification: SovereignQualificationReceipt) -> None:
    _require(document.get("type") == "FeatureCollection", "public derivative must be a FeatureCollection")
    features = document.get("features")
    _require(isinstance(features, list) and len(features) == 1, "public derivative must contain exactly one feature")
    feature = features[0]
    properties = feature.get("properties", {})
    geometry = normalize_boundary_geometry(feature.get("geometry"))
    _require(properties.get("sourceBoundaryId") == qualification.boundary_id, "derivative boundary lineage mismatch")
    _require(properties.get("sourceBoundaryVersion") == qualification.boundary_version, "derivative source version mismatch")
    _require(properties.get("sourceQualificationReceiptSha256") == qualification.receipt_sha256, "derivative qualification fingerprint mismatch")
    _require(properties.get("visibility") == "public", "boundary derivative must remain public")
    _require(properties.get("runtimePublicationDeferredTo") == "P004.M1.5", "10B derivatives must not claim runtime publication")
    _require(properties.get("offshoreIslandCount") == qualification.offshore_island_count, "derivative must preserve offshore island count")
    _require(len(geometry["coordinates"]) == qualification.polygon_count, "derivative polygon count mismatch")
    _require(properties.get("derivativeGeometrySha256") == canonical_sha256(geometry), "derivative geometry fingerprint mismatch")
