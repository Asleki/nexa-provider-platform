"""P004.M1.1-P004.M1.2 high-resolution sovereign-boundary authoring validation.

This module validates authoring contracts and source provenance only. It does not
qualify, approve, supersede, publish, or persist a sovereign boundary.
"""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .geometry import boundary_extent, normalize_boundary_geometry


class BoundaryAuthoringError(ValueError):
    """Raised when a high-resolution source package violates its authoring contract."""


@dataclass(frozen=True, slots=True)
class BoundaryAuthoringReceipt:
    source_package_id: str
    boundary_id: str
    boundary_version: int
    authoring_contract_id: str
    status: str
    polygon_count: int
    ring_count: int
    unique_vertex_count: int
    mainland_vertex_count: int
    offshore_island_count: int
    extent: tuple[float, float, float, float]
    source_package_sha256: str


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BoundaryAuthoringError(f"cannot read JSON artifact {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BoundaryAuthoringError(f"JSON artifact must contain an object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise BoundaryAuthoringError(f"cannot fingerprint artifact {path}: {exc}") from exc
    return digest.hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BoundaryAuthoringError(message)


def validate_authoring_contract(contract: dict[str, Any]) -> None:
    _require(contract.get("contractId") == "boundary-authoring-contract:novegeo:sovereign:v001", "unexpected authoring contract identity")
    _require(contract.get("contractVersion") == 1, "unsupported authoring contract version")
    _require(contract.get("boundaryId") == "boundary:novegeo:sovereign", "authoring contract boundary identity mismatch")
    _require(contract.get("coordinateReferenceId") == "crs:novegeo:geographic", "authoring contract CRS mismatch")
    _require(contract.get("coordinateReferenceVersion") == 1, "authoring contract CRS version mismatch")
    _require(contract.get("applicationAxisOrder") == ["longitude", "latitude"], "authoring axis order must be longitude, latitude")
    _require(contract.get("normalizedGeometryType") == "MultiPolygon", "authoring geometry must normalize to MultiPolygon")
    precision = contract.get("authoringPrecisionDecimalPlacesMax")
    _require(isinstance(precision, int) and 1 <= precision <= 8, "authoring precision must be between 1 and 8 decimal places")
    spatial = contract.get("spatialPolicy", {})
    _require(spatial.get("antimeridianCrossingAllowed") is False, "v001 authoring contract must forbid antimeridian crossing")
    _require(spatial.get("equatorCrossingExpected") is True, "NoveGeo authoring contract must expect equator crossing")
    policy = contract.get("authoringPolicy", {})
    for key in (
        "artificialVertexDensificationForbidden",
        "meaninglessRandomJitterForbidden",
        "macroMesoMicroDetailRequired",
        "mixedNaturalAndTreatyBorderCharacterRequired",
        "mainlandDominantWithOffshoreIslandsRequired",
    ):
        _require(policy.get(key) is True, f"authoring policy must enable {key}")


def _read_feature_collection(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    document = _load_json(path)
    _require(document.get("type") == "FeatureCollection", "boundary artifact must be a GeoJSON FeatureCollection")
    features = document.get("features")
    _require(isinstance(features, list) and len(features) == 1, "boundary artifact must contain exactly one feature")
    feature = features[0]
    _require(isinstance(feature, dict) and feature.get("type") == "Feature", "boundary artifact must contain a GeoJSON Feature")
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    _require(isinstance(properties, dict), "boundary feature properties are required")
    _require(isinstance(geometry, dict), "boundary feature geometry is required")
    return properties, geometry


def _geometry_counts(normalized: dict[str, Any]) -> tuple[int, int, int, int, int]:
    polygons = normalized["coordinates"]
    polygon_count = len(polygons)
    ring_count = sum(len(polygon) for polygon in polygons)
    unique_vertex_count = sum(len(ring) - 1 for polygon in polygons for ring in polygon)
    mainland_vertex_count = len(polygons[0][0]) - 1
    offshore_island_count = polygon_count - 1
    return polygon_count, ring_count, unique_vertex_count, mainland_vertex_count, offshore_island_count


def _validate_vertex_csv(path: Path, source_geometry: dict[str, Any]) -> None:
    expected: list[tuple[str, str, int, float, float]] = []
    geometry_type = source_geometry.get("type")
    coordinates = source_geometry.get("coordinates")
    if geometry_type == "Polygon":
        polygons = [coordinates]
    elif geometry_type == "MultiPolygon":
        polygons = coordinates
    else:
        raise BoundaryAuthoringError("vertex CSV source geometry must be Polygon or MultiPolygon")
    for polygon_index, polygon in enumerate(polygons, start=1):
        for ring_index, ring in enumerate(polygon, start=1):
            for sequence, (longitude, latitude) in enumerate(ring):
                expected.append((f"polygon-{polygon_index:02d}", f"ring-{ring_index:02d}", sequence, float(longitude), float(latitude)))
    actual: list[tuple[str, str, int, float, float]] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            _require(reader.fieldnames == ["polygon_id", "ring_id", "vertex_sequence", "longitude", "latitude", "vertex_role"], "vertex CSV header mismatch")
            for row in reader:
                actual.append((row["polygon_id"], row["ring_id"], int(row["vertex_sequence"]), float(row["longitude"]), float(row["latitude"])))
    except (OSError, ValueError, KeyError) as exc:
        raise BoundaryAuthoringError(f"cannot validate vertex CSV: {exc}") from exc
    _require(actual == expected, "vertex CSV must exactly reproduce the candidate GeoJSON vertex sequence")




def _validate_segment_ledger(path: Path, mainland_vertex_count: int, offshore_island_count: int) -> None:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        raise BoundaryAuthoringError(f"cannot validate segment ledger: {exc}") from exc
    _require(bool(rows), "segment ledger must contain authored boundary segments")
    mainland = [row for row in rows if row.get("polygon_id") == "polygon-01"]
    _require(mainland, "segment ledger must describe the mainland boundary")
    starts = [int(row["start_vertex_sequence"]) for row in mainland]
    ends = [int(row["end_vertex_sequence"]) for row in mainland]
    _require(starts[0] == 0, "mainland segment ledger must begin at vertex 0")
    _require(ends[-1] == mainland_vertex_count - 1, "mainland segment ledger must cover the final unique mainland vertex")
    for previous, current in zip(ends, starts[1:]):
        _require(current == previous + 1, "mainland segment ledger must cover vertices without gaps or overlaps")
    characters = {row.get("boundary_character") for row in mainland}
    _require("natural_coastline" in characters, "segment ledger must identify natural coastline")
    _require("straight_treaty_border" in characters, "segment ledger must identify treaty border sections")
    reserved_features = {row.get("future_geographic_feature_reserve") for row in mainland}
    for feature in {"bay", "cape", "estuary", "natural_harbour", "long_beach", "cliff"}:
        _require(feature in reserved_features, f"segment ledger must reserve {feature}")
    island_rows = [row for row in rows if row.get("boundary_character") == "offshore_island_coastline"]
    _require(len(island_rows) == offshore_island_count, "segment ledger island count mismatch")


def validate_boundary_source_package(world_boundary_root: Path, source_package_relative_path: str = "provenance/novegeo_world_boundary_v002_source-package.json") -> BoundaryAuthoringReceipt:
    root = Path(world_boundary_root)
    package_path = root / source_package_relative_path
    package = _load_json(package_path)

    _require(package.get("sourcePackageId") == "source-package:novegeo:world-boundary:v002", "unexpected v002 source package identity")
    _require(package.get("datasetId") == "dataset:novegeo:world-boundary", "dataset identity mismatch")
    _require(package.get("datasetVersion") == 2, "v002 source package must use dataset version 2")
    _require(package.get("boundaryId") == "boundary:novegeo:sovereign", "boundary identity mismatch")
    _require(package.get("boundaryVersion") == 2, "v002 source package must use boundary version 2")
    _require(package.get("supersedesBoundaryVersion") == 1, "v002 candidate must declare v001 as its proposed predecessor")
    _require(package.get("lifecycleStatus") == "candidate", "Bundle 10A must leave v002 as candidate")
    _require(package.get("runtimeMode") == "shared_reference", "sovereign geography must remain shared_reference")
    _require(package.get("applicationAxisOrder") == ["longitude", "latitude"], "source package axis order mismatch")
    _require(package.get("qualificationDeferredTo") == "P004.M1.3", "qualification must remain deferred to P004.M1.3")
    _require(package.get("publicDerivativeGenerationDeferredTo") == "P004.M1.4", "public derivatives must remain deferred to P004.M1.4")

    artifacts = package.get("artifacts")
    _require(isinstance(artifacts, dict), "source package artifacts are required")
    required_artifacts = {"authoringContract", "designBrief", "rawGeoJson", "candidateGeoJson", "vertexCsv", "segmentLedger"}
    _require(required_artifacts.issubset(artifacts), "source package is missing required artifacts")
    for name in required_artifacts:
        entry = artifacts[name]
        _require(isinstance(entry, dict), f"artifact entry must be an object: {name}")
        relative = entry.get("path")
        _require(isinstance(relative, str) and relative and not Path(relative).is_absolute(), f"artifact path must be relative: {name}")
        artifact_path = root / relative
        _require(artifact_path.is_file(), f"artifact does not exist: {relative}")
        _require(entry.get("sha256") == _sha256(artifact_path), f"artifact fingerprint mismatch: {relative}")

    contract = _load_json(root / artifacts["authoringContract"]["path"])
    validate_authoring_contract(contract)
    _require(package.get("authoringContractId") == contract.get("contractId"), "source package authoring contract reference mismatch")

    design_brief = _load_json(root / artifacts["designBrief"]["path"])
    _require(design_brief.get("designBriefId") == package.get("designBriefId"), "design brief reference mismatch")
    _require(design_brief.get("candidateBoundaryVersion") == 2, "design brief must target boundary v002")
    _require(design_brief.get("nationalForm", {}).get("mainlandDominant") is True, "design brief must require mainland dominance")
    _require(design_brief.get("nationalForm", {}).get("offshoreIslands") is True, "design brief must require offshore islands")

    raw_path = root / artifacts["rawGeoJson"]["path"]
    candidate_path = root / artifacts["candidateGeoJson"]["path"]
    _require(raw_path.read_bytes() == candidate_path.read_bytes(), "Bundle 10A candidate must preserve the authored raw geometry unchanged")
    properties, geometry = _read_feature_collection(candidate_path)
    _require(properties.get("boundaryId") == package.get("boundaryId"), "candidate boundary identity mismatch")
    _require(properties.get("boundaryVersion") == 2, "candidate boundary version mismatch")
    _require(properties.get("datasetVersion") == 2, "candidate dataset version mismatch")
    _require(properties.get("sourcePackageId") == package.get("sourcePackageId"), "candidate source package reference mismatch")
    _require(properties.get("authoringContractId") == package.get("authoringContractId"), "candidate authoring contract reference mismatch")
    _require(properties.get("lifecycleStatus") == "candidate", "candidate must not be qualified or active in Bundle 10A")

    normalized = normalize_boundary_geometry(geometry)
    polygon_count, ring_count, unique_vertex_count, mainland_vertex_count, offshore_island_count = _geometry_counts(normalized)
    extent = boundary_extent(normalized)
    _require(extent[1] < 0.0 < extent[3], "NoveGeo v002 candidate must cross the equator")
    _require(unique_vertex_count >= 750, "high-resolution candidate must contain at least 750 unique governed boundary vertices")
    _require(mainland_vertex_count >= 500, "high-resolution mainland must contain at least 500 governed vertices")
    _require(offshore_island_count >= 3, "mainland-with-islands brief requires at least three offshore island polygons")
    _require(mainland_vertex_count > unique_vertex_count - mainland_vertex_count, "mainland must remain dominant by authored vertex count")

    statistics = package.get("statistics", {})
    _require(statistics.get("polygonCount") == polygon_count, "source package polygon count mismatch")
    _require(statistics.get("ringCount") == ring_count, "source package ring count mismatch")
    _require(statistics.get("uniqueBoundaryVertexCount") == unique_vertex_count, "source package vertex count mismatch")
    _require(statistics.get("mainlandUniqueVertexCount") == mainland_vertex_count, "source package mainland vertex count mismatch")
    _require(statistics.get("offshoreIslandCount") == offshore_island_count, "source package island count mismatch")

    _validate_vertex_csv(root / artifacts["vertexCsv"]["path"], geometry)
    _validate_segment_ledger(root / artifacts["segmentLedger"]["path"], mainland_vertex_count, offshore_island_count)

    return BoundaryAuthoringReceipt(
        source_package_id=package["sourcePackageId"],
        boundary_id=package["boundaryId"],
        boundary_version=package["boundaryVersion"],
        authoring_contract_id=package["authoringContractId"],
        status="authoring_validated_candidate",
        polygon_count=polygon_count,
        ring_count=ring_count,
        unique_vertex_count=unique_vertex_count,
        mainland_vertex_count=mainland_vertex_count,
        offshore_island_count=offshore_island_count,
        extent=extent,
        source_package_sha256=_sha256(package_path),
    )
