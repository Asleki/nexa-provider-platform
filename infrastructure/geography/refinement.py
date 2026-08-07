"""P004.M1.3 sovereign-boundary qualification and supersession governance.

This module strengthens the locked P004 world-geometry authority without changing
its runtime publication service. It qualifies the authored v002 source package and
records explicit v001 -> v002 supersession lineage. Runtime activation remains a
separate publication concern for P004.M1.5.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .authoring import BoundaryAuthoringReceipt, validate_boundary_source_package
from .geometry import boundary_extent, canonical_sha256, normalize_boundary_geometry


class BoundaryRefinementError(ValueError):
    """Raised when v002 cannot be qualified or its supersession lineage is unsafe."""


@dataclass(frozen=True, slots=True)
class QualificationFinding:
    code: str
    passed: bool
    message: str


@dataclass(frozen=True, slots=True)
class SovereignQualificationReceipt:
    qualification_id: str
    boundary_id: str
    boundary_version: int
    dataset_id: str
    dataset_version: int
    source_package_id: str
    supersedes_boundary_version: int
    coordinate_reference_id: str
    coordinate_reference_version: int
    runtime_mode: str
    decision: str
    lifecycle_status: str
    polygon_count: int
    ring_count: int
    unique_vertex_count: int
    mainland_vertex_count: int
    offshore_island_count: int
    extent: tuple[float, float, float, float]
    source_geometry_sha256: str
    normalized_geometry_sha256: str
    source_package_sha256: str
    receipt_sha256: str
    findings: tuple[QualificationFinding, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "qualificationId": self.qualification_id,
            "boundaryId": self.boundary_id,
            "boundaryVersion": self.boundary_version,
            "datasetId": self.dataset_id,
            "datasetVersion": self.dataset_version,
            "sourcePackageId": self.source_package_id,
            "supersedesBoundaryVersion": self.supersedes_boundary_version,
            "coordinateReferenceId": self.coordinate_reference_id,
            "coordinateReferenceVersion": self.coordinate_reference_version,
            "runtimeMode": self.runtime_mode,
            "decision": self.decision,
            "lifecycleStatus": self.lifecycle_status,
            "polygonCount": self.polygon_count,
            "ringCount": self.ring_count,
            "uniqueVertexCount": self.unique_vertex_count,
            "mainlandVertexCount": self.mainland_vertex_count,
            "offshoreIslandCount": self.offshore_island_count,
            "extent": {
                "minLongitude": self.extent[0],
                "minLatitude": self.extent[1],
                "maxLongitude": self.extent[2],
                "maxLatitude": self.extent[3],
            },
            "sourceGeometrySha256": self.source_geometry_sha256,
            "normalizedGeometrySha256": self.normalized_geometry_sha256,
            "sourcePackageSha256": self.source_package_sha256,
            "receiptSha256": self.receipt_sha256,
            "findings": [asdict(finding) for finding in self.findings],
        }


@dataclass(frozen=True, slots=True)
class BoundarySupersessionReceipt:
    supersession_id: str
    boundary_id: str
    predecessor_version: int
    successor_version: int
    predecessor_prior_lifecycle: str
    predecessor_result_lifecycle: str
    successor_prior_lifecycle: str
    successor_result_lifecycle: str
    decision: str
    qualification_id: str
    qualification_receipt_sha256: str
    runtime_activation_deferred_to: str
    historical_predecessor_retained: bool
    receipt_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "supersessionId": self.supersession_id,
            "boundaryId": self.boundary_id,
            "predecessorVersion": self.predecessor_version,
            "successorVersion": self.successor_version,
            "predecessorPriorLifecycle": self.predecessor_prior_lifecycle,
            "predecessorResultLifecycle": self.predecessor_result_lifecycle,
            "successorPriorLifecycle": self.successor_prior_lifecycle,
            "successorResultLifecycle": self.successor_result_lifecycle,
            "decision": self.decision,
            "qualificationId": self.qualification_id,
            "qualificationReceiptSha256": self.qualification_receipt_sha256,
            "runtimeActivationDeferredTo": self.runtime_activation_deferred_to,
            "historicalPredecessorRetained": self.historical_predecessor_retained,
            "receiptSha256": self.receipt_sha256,
        }


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise BoundaryRefinementError(message)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BoundaryRefinementError(f"cannot read JSON artifact {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BoundaryRefinementError(f"JSON artifact must contain an object: {path}")
    return value


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise BoundaryRefinementError(f"cannot fingerprint artifact {path}: {exc}") from exc
    return digest.hexdigest()


def _feature(document: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    _require(document.get("type") == "FeatureCollection", "boundary artifact must be a FeatureCollection")
    features = document.get("features")
    _require(isinstance(features, list) and len(features) == 1, "boundary artifact must contain exactly one feature")
    feature = features[0]
    _require(isinstance(feature, dict) and feature.get("type") == "Feature", "boundary artifact feature is invalid")
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    _require(isinstance(properties, dict), "boundary properties are required")
    _require(isinstance(geometry, dict), "boundary geometry is required")
    return properties, geometry


def _counts(normalized: dict[str, Any]) -> tuple[int, int, int, int, int]:
    polygons = normalized["coordinates"]
    polygon_count = len(polygons)
    ring_count = sum(len(polygon) for polygon in polygons)
    unique_vertex_count = sum(len(ring) - 1 for polygon in polygons for ring in polygon)
    mainland_vertex_count = len(polygons[0][0]) - 1
    offshore_island_count = polygon_count - 1
    return polygon_count, ring_count, unique_vertex_count, mainland_vertex_count, offshore_island_count


def _receipt_hash(payload: dict[str, Any]) -> str:
    return canonical_sha256(payload)


def qualify_v002_boundary(world_boundary_root: Path) -> SovereignQualificationReceipt:
    """Qualify the authored v002 candidate without activating it in the locked P004 runtime."""
    root = Path(world_boundary_root)
    authoring: BoundaryAuthoringReceipt = validate_boundary_source_package(root)
    candidate_path = root / "candidate/novegeo_world_boundary_v002.geojson"
    predecessor_path = root / "qualified/novegeo_world_boundary_v001.geojson"
    package_path = root / "provenance/novegeo_world_boundary_v002_source-package.json"

    candidate = _load_json(candidate_path)
    predecessor = _load_json(predecessor_path)
    package = _load_json(package_path)
    properties, geometry = _feature(candidate)
    predecessor_properties, predecessor_geometry = _feature(predecessor)
    normalized = normalize_boundary_geometry(geometry)
    predecessor_normalized = normalize_boundary_geometry(predecessor_geometry)

    findings: list[QualificationFinding] = []

    def check(code: str, condition: bool, message: str) -> None:
        if not condition:
            raise BoundaryRefinementError(message)
        findings.append(QualificationFinding(code=code, passed=True, message=message))

    check("AUTHORING_PACKAGE_VALID", authoring.status == "authoring_validated_candidate", "10A authoring package validates deterministically")
    check("BOUNDARY_ID_CONTINUITY", properties.get("boundaryId") == predecessor_properties.get("boundaryId") == "boundary:novegeo:sovereign", "stable sovereign boundary identity is preserved")
    check("VERSION_LINEAGE", properties.get("boundaryVersion") == 2 and properties.get("supersedesBoundaryVersion") == 1 and predecessor_properties.get("boundaryVersion") == 1, "v002 explicitly supersedes v001")
    check("DATASET_LINEAGE", properties.get("datasetId") == predecessor_properties.get("datasetId") == "dataset:novegeo:world-boundary" and properties.get("datasetVersion") == 2, "dataset family is stable and v002 uses dataset version 2")
    check("CRS_CONTINUITY", properties.get("coordinateReferenceId") == predecessor_properties.get("coordinateReferenceId") == "crs:novegeo:geographic" and properties.get("coordinateReferenceVersion") == 1, "coordinate-reference identity remains stable")
    check("RUNTIME_SHARED_REFERENCE", properties.get("runtimeMode") == predecessor_properties.get("runtimeMode") == "shared_reference", "sovereign geography remains shared_reference")
    check("PUBLIC_VISIBILITY", properties.get("visibility") == "public", "sovereign boundary remains public reference geography")
    check("CANDIDATE_LIFECYCLE", properties.get("lifecycleStatus") == "candidate", "source artifact remains an immutable candidate input")

    polygon_count, ring_count, unique_vertex_count, mainland_vertex_count, offshore_island_count = _counts(normalized)
    check("MAINLAND_AND_ISLANDS", polygon_count == 6 and offshore_island_count == 5, "qualified geometry preserves one mainland and five offshore islands")
    check("HIGH_RESOLUTION_INTEGRITY", unique_vertex_count == authoring.unique_vertex_count and mainland_vertex_count == authoring.mainland_vertex_count, "qualification preserves every authored source vertex")

    extent = boundary_extent(normalized)
    check("EXTENT_INTEGRITY", extent == authoring.extent, "qualified extent exactly matches the authoring receipt")
    check("EQUATOR_CROSSING", extent[1] < 0.0 < extent[3], "NoveGeo continues to cross the equator")
    check("NO_ANTIMERIDIAN", (extent[2] - extent[0]) < 180.0, "v002 does not cross the antimeridian")
    check("PREDECESSOR_PRESERVED", predecessor_properties.get("lifecycleStatus") == "qualified" and predecessor_normalized["type"] == "MultiPolygon", "historical v001 qualified artifact remains intact")
    check("SOURCE_PACKAGE_MATCH", package.get("sourcePackageId") == properties.get("sourcePackageId") == authoring.source_package_id, "candidate and provenance share the same source-package identity")

    source_geometry_sha256 = canonical_sha256(geometry)
    normalized_geometry_sha256 = canonical_sha256(normalized)
    canonical_payload = {
        "qualificationId": "qualification:novegeo:world-boundary:v002",
        "boundaryId": properties["boundaryId"],
        "boundaryVersion": 2,
        "datasetId": properties["datasetId"],
        "datasetVersion": 2,
        "sourcePackageId": properties["sourcePackageId"],
        "supersedesBoundaryVersion": 1,
        "coordinateReferenceId": properties["coordinateReferenceId"],
        "coordinateReferenceVersion": properties["coordinateReferenceVersion"],
        "runtimeMode": properties["runtimeMode"],
        "decision": "qualified",
        "lifecycleStatus": "qualified",
        "polygonCount": polygon_count,
        "ringCount": ring_count,
        "uniqueVertexCount": unique_vertex_count,
        "mainlandVertexCount": mainland_vertex_count,
        "offshoreIslandCount": offshore_island_count,
        "extent": list(extent),
        "sourceGeometrySha256": source_geometry_sha256,
        "normalizedGeometrySha256": normalized_geometry_sha256,
        "sourcePackageSha256": _file_sha256(package_path),
        "findingCodes": [finding.code for finding in findings],
    }
    receipt_sha256 = _receipt_hash(canonical_payload)
    return SovereignQualificationReceipt(
        qualification_id=canonical_payload["qualificationId"],
        boundary_id=properties["boundaryId"],
        boundary_version=2,
        dataset_id=properties["datasetId"],
        dataset_version=2,
        source_package_id=properties["sourcePackageId"],
        supersedes_boundary_version=1,
        coordinate_reference_id=properties["coordinateReferenceId"],
        coordinate_reference_version=properties["coordinateReferenceVersion"],
        runtime_mode=properties["runtimeMode"],
        decision="qualified",
        lifecycle_status="qualified",
        polygon_count=polygon_count,
        ring_count=ring_count,
        unique_vertex_count=unique_vertex_count,
        mainland_vertex_count=mainland_vertex_count,
        offshore_island_count=offshore_island_count,
        extent=extent,
        source_geometry_sha256=source_geometry_sha256,
        normalized_geometry_sha256=normalized_geometry_sha256,
        source_package_sha256=canonical_payload["sourcePackageSha256"],
        receipt_sha256=receipt_sha256,
        findings=tuple(findings),
    )


def build_v001_to_v002_supersession(world_boundary_root: Path, qualification: SovereignQualificationReceipt | None = None) -> BoundarySupersessionReceipt:
    """Record governed supersession lineage while deferring runtime activation to 10C."""
    root = Path(world_boundary_root)
    qualification = qualification or qualify_v002_boundary(root)
    predecessor = _load_json(root / "qualified/novegeo_world_boundary_v001.geojson")
    candidate = _load_json(root / "candidate/novegeo_world_boundary_v002.geojson")
    predecessor_properties, _ = _feature(predecessor)
    candidate_properties, _ = _feature(candidate)

    _require(qualification.decision == "qualified", "only a qualified successor may supersede v001")
    _require(predecessor_properties.get("boundaryVersion") == 1, "supersession predecessor must be v001")
    _require(candidate_properties.get("boundaryVersion") == 2, "supersession successor must be v002")
    _require(candidate_properties.get("supersedesBoundaryVersion") == 1, "v002 must explicitly declare v001 as predecessor")
    _require(predecessor_properties.get("boundaryId") == qualification.boundary_id == candidate_properties.get("boundaryId"), "supersession cannot change sovereign identity")

    canonical_payload = {
        "supersessionId": "supersession:novegeo:world-boundary:v001-to-v002",
        "boundaryId": qualification.boundary_id,
        "predecessorVersion": 1,
        "successorVersion": 2,
        "predecessorPriorLifecycle": predecessor_properties.get("lifecycleStatus"),
        "predecessorResultLifecycle": "superseded",
        "successorPriorLifecycle": candidate_properties.get("lifecycleStatus"),
        "successorResultLifecycle": "qualified",
        "decision": "supersession_approved",
        "qualificationId": qualification.qualification_id,
        "qualificationReceiptSha256": qualification.receipt_sha256,
        "runtimeActivationDeferredTo": "P004.M1.5",
        "historicalPredecessorRetained": True,
    }
    return BoundarySupersessionReceipt(
        supersession_id=canonical_payload["supersessionId"],
        boundary_id=qualification.boundary_id,
        predecessor_version=1,
        successor_version=2,
        predecessor_prior_lifecycle=str(predecessor_properties.get("lifecycleStatus")),
        predecessor_result_lifecycle="superseded",
        successor_prior_lifecycle=str(candidate_properties.get("lifecycleStatus")),
        successor_result_lifecycle="qualified",
        decision="supersession_approved",
        qualification_id=qualification.qualification_id,
        qualification_receipt_sha256=qualification.receipt_sha256,
        runtime_activation_deferred_to="P004.M1.5",
        historical_predecessor_retained=True,
        receipt_sha256=_receipt_hash(canonical_payload),
    )
