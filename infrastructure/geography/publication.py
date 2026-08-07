"""P004.M1.5 governed multi-resolution publication for NoveGeo sovereign v002.

This module activates the already-qualified v002 source through public-safe
standard and overview derivatives. It does not mutate the locked P004 geometry
service and does not introduce map interaction or registry overlays.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class MultiResolutionPublicationError(ValueError):
    """Raised when governed publication lineage or representation selection fails."""


@dataclass(frozen=True, slots=True)
class BoundaryRepresentation:
    resolution_class: str
    derivative_id: str
    derivative_version: int
    vertex_count: int
    polygon_count: int
    offshore_island_count: int
    geometry_sha256: str
    content_sha256: str
    asset_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolutionClass": self.resolution_class,
            "derivativeId": self.derivative_id,
            "derivativeVersion": self.derivative_version,
            "vertexCount": self.vertex_count,
            "polygonCount": self.polygon_count,
            "offshoreIslandCount": self.offshore_island_count,
            "geometrySha256": self.geometry_sha256,
            "contentSha256": self.content_sha256,
            "assetPath": self.asset_path,
        }


@dataclass(frozen=True, slots=True)
class MultiResolutionBoundaryPublication:
    publication_id: str
    publication_version: int
    boundary_id: str
    boundary_version: int
    dataset_id: str
    dataset_version: int
    qualification_id: str
    qualification_receipt_sha256: str
    coordinate_reference_id: str
    coordinate_reference_version: int
    runtime_mode: str
    visibility: str
    lifecycle_status: str
    default_resolution: str
    source_authoritative_vertex_count: int
    predecessor_boundary_version: int
    representations: tuple[BoundaryRepresentation, ...]
    content_sha256: str

    def select(self, resolution: str | None = None) -> BoundaryRepresentation:
        requested = self.default_resolution if resolution in (None, "") else resolution
        for representation in self.representations:
            if representation.resolution_class == requested:
                return representation
        raise MultiResolutionPublicationError(f"unsupported map resolution: {requested}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "publicationId": self.publication_id,
            "publicationVersion": self.publication_version,
            "boundaryId": self.boundary_id,
            "boundaryVersion": self.boundary_version,
            "datasetId": self.dataset_id,
            "datasetVersion": self.dataset_version,
            "qualificationId": self.qualification_id,
            "qualificationReceiptSha256": self.qualification_receipt_sha256,
            "coordinateReference": {
                "coordinateReferenceId": self.coordinate_reference_id,
                "version": self.coordinate_reference_version,
                "authorityName": "EPSG",
                "authorityCode": "4326",
                "axisOrder": ["longitude", "latitude"],
                "unit": "decimal_degrees",
            },
            "runtimeMode": self.runtime_mode,
            "visibility": self.visibility,
            "lifecycleStatus": self.lifecycle_status,
            "defaultResolution": self.default_resolution,
            "representations": [item.to_dict() for item in self.representations],
            "sourceAuthoritativeVertexCount": self.source_authoritative_vertex_count,
            "activation": {
                "active": True,
                "activatedByMilestone": "P004.M1.5",
                "predecessorBoundaryVersion": self.predecessor_boundary_version,
            },
            "contentSha256": self.content_sha256,
        }


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MultiResolutionPublicationError(f"cannot read publication artifact {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise MultiResolutionPublicationError(f"publication artifact must be an object: {path}")
    return payload


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _feature(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    if payload.get("type") != "FeatureCollection":
        raise MultiResolutionPublicationError("derivative must be a FeatureCollection")
    features = payload.get("features")
    if not isinstance(features, list) or len(features) != 1:
        raise MultiResolutionPublicationError("derivative must contain exactly one feature")
    feature = features[0]
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise MultiResolutionPublicationError("derivative feature is invalid")
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        raise MultiResolutionPublicationError("derivative properties and geometry are required")
    if geometry.get("type") != "MultiPolygon":
        raise MultiResolutionPublicationError("derivative geometry must use MultiPolygon")
    return properties, geometry


def _representation(root: Path, resolution: str) -> BoundaryRepresentation:
    path = root / f"derivatives/v002/novegeo_world_boundary_v002_{resolution}.geojson"
    payload = _load_json(path)
    properties, _ = _feature(payload)

    required = {
        "resolutionClass": resolution,
        "sourceBoundaryId": "boundary:novegeo:sovereign",
        "sourceBoundaryVersion": 2,
        "sourceQualificationId": "qualification:novegeo:world-boundary:v002",
        "datasetId": "dataset:novegeo:world-boundary",
        "datasetVersion": 2,
        "coordinateReferenceId": "crs:novegeo:geographic",
        "coordinateReferenceVersion": 1,
        "runtimeMode": "shared_reference",
        "visibility": "public",
        "polygonCount": 6,
        "offshoreIslandCount": 5,
    }
    for key, expected in required.items():
        if properties.get(key) != expected:
            raise MultiResolutionPublicationError(
                f"{resolution} derivative {key} expected {expected!r}, got {properties.get(key)!r}"
            )

    return BoundaryRepresentation(
        resolution_class=resolution,
        derivative_id=str(properties["derivativeId"]),
        derivative_version=int(properties["derivativeVersion"]),
        vertex_count=int(properties["derivativeVertexCount"]),
        polygon_count=int(properties["polygonCount"]),
        offshore_island_count=int(properties["offshoreIslandCount"]),
        geometry_sha256=str(properties["derivativeGeometrySha256"]),
        content_sha256=str(properties["contentSha256"]),
        asset_path=f"./public/geography/novegeo/world-boundary/v002/{resolution}.geojson",
    )


def build_v002_multi_resolution_publication(world_boundary_root: Path) -> MultiResolutionBoundaryPublication:
    """Build and validate the active public v002 publication catalogue."""
    root = Path(world_boundary_root)
    qualification = _load_json(root / "qualification/novegeo_world_boundary_v002_qualification.json")
    supersession = _load_json(root / "supersession/novegeo_world_boundary_v001_to_v002.json")

    if qualification.get("decision") != "qualified" or qualification.get("boundaryVersion") != 2:
        raise MultiResolutionPublicationError("v002 must be qualified before publication")
    if supersession.get("decision") != "supersession_approved":
        raise MultiResolutionPublicationError("v001 to v002 supersession must be approved before publication")
    if supersession.get("successorVersion") != 2 or supersession.get("predecessorVersion") != 1:
        raise MultiResolutionPublicationError("supersession lineage is invalid")
    if supersession.get("qualificationReceiptSha256") != qualification.get("receiptSha256"):
        raise MultiResolutionPublicationError("supersession does not reference the active qualification receipt")

    overview = _representation(root, "overview")
    standard = _representation(root, "standard")

    base = {
        "publicationId": "publication:novegeo:world-boundary:v002",
        "publicationVersion": 2,
        "boundaryId": "boundary:novegeo:sovereign",
        "boundaryVersion": 2,
        "datasetId": "dataset:novegeo:world-boundary",
        "datasetVersion": 2,
        "qualificationId": str(qualification["qualificationId"]),
        "qualificationReceiptSha256": str(qualification["receiptSha256"]),
        "coordinateReference": {
            "coordinateReferenceId": "crs:novegeo:geographic",
            "version": 1,
            "authorityName": "EPSG",
            "authorityCode": "4326",
            "axisOrder": ["longitude", "latitude"],
            "unit": "decimal_degrees",
        },
        "runtimeMode": "shared_reference",
        "visibility": "public",
        "lifecycleStatus": "published",
        "defaultResolution": "standard",
        "representations": [overview.to_dict(), standard.to_dict()],
        "sourceAuthoritativeVertexCount": int(qualification["uniqueVertexCount"]),
        "activation": {
            "active": True,
            "activatedByMilestone": "P004.M1.5",
            "predecessorBoundaryVersion": 1,
        },
    }
    content_sha256 = _canonical_sha256(base)

    return MultiResolutionBoundaryPublication(
        publication_id=base["publicationId"],
        publication_version=base["publicationVersion"],
        boundary_id=base["boundaryId"],
        boundary_version=base["boundaryVersion"],
        dataset_id=base["datasetId"],
        dataset_version=base["datasetVersion"],
        qualification_id=base["qualificationId"],
        qualification_receipt_sha256=base["qualificationReceiptSha256"],
        coordinate_reference_id="crs:novegeo:geographic",
        coordinate_reference_version=1,
        runtime_mode=base["runtimeMode"],
        visibility=base["visibility"],
        lifecycle_status=base["lifecycleStatus"],
        default_resolution=base["defaultResolution"],
        source_authoritative_vertex_count=base["sourceAuthoritativeVertexCount"],
        predecessor_boundary_version=1,
        representations=(overview, standard),
        content_sha256=content_sha256,
    )
