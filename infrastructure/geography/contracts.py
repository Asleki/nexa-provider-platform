"""Framework-independent geography contracts for P004.1 and P004.2."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BoundaryIdentity:
    boundary_id: str
    version: int

    def __post_init__(self) -> None:
        if not self.boundary_id.startswith("boundary:"):
            raise ValueError("boundary_id must be namespaced with 'boundary:'")
        if self.version < 1:
            raise ValueError("boundary version must be positive")


@dataclass(frozen=True, slots=True)
class CoordinateReference:
    coordinate_reference_id: str = "crs:novegeo:geographic"
    version: int = 1
    authority_name: str = "EPSG"
    authority_code: str = "4326"
    axis_order: tuple[str, str] = ("longitude", "latitude")
    unit: str = "decimal_degrees"

    def __post_init__(self) -> None:
        if not self.coordinate_reference_id.startswith("crs:"):
            raise ValueError("coordinate_reference_id must be namespaced with 'crs:'")
        if self.version < 1:
            raise ValueError("coordinate reference version must be positive")
        if self.axis_order != ("longitude", "latitude"):
            raise ValueError("application coordinate order must be longitude, latitude")


@dataclass(frozen=True, slots=True)
class GeographicCoordinate:
    longitude: float
    latitude: float

    def __post_init__(self) -> None:
        import math

        if not math.isfinite(self.longitude) or not math.isfinite(self.latitude):
            raise ValueError("coordinates must be finite")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")

    def to_pair(self) -> tuple[float, float]:
        return (self.longitude, self.latitude)


@dataclass(frozen=True, slots=True)
class ProjectedCoordinate:
    x: float
    y: float
    projection_id: str
    projection_version: int


@dataclass(frozen=True, slots=True)
class WorldBoundaryCandidate:
    identity: BoundaryIdentity
    dataset_id: str
    dataset_version: int
    source_package_id: str
    coordinate_reference: CoordinateReference
    geometry: dict[str, Any]
    runtime_mode: str = "shared_reference"
    visibility: str = "public"
    lifecycle_status: str = "candidate"

    def __post_init__(self) -> None:
        if not self.dataset_id.startswith("dataset:"):
            raise ValueError("dataset_id must be namespaced with 'dataset:'")
        if self.dataset_version < 1:
            raise ValueError("dataset_version must be positive")
        if not self.source_package_id.startswith("source-package:"):
            raise ValueError("source_package_id must be namespaced")
        if self.runtime_mode not in {"production", "simulation", "shared_reference"}:
            raise ValueError("unsupported runtime_mode")
        if self.visibility not in {"public", "internal", "restricted", "confidential"}:
            raise ValueError("unsupported visibility")


@dataclass(frozen=True, slots=True)
class WorldBoundaryPublication:
    publication_id: str
    identity: BoundaryIdentity
    dataset_id: str
    dataset_version: int
    coordinate_reference: CoordinateReference
    geometry: dict[str, Any]
    extent: tuple[float, float, float, float]
    source_sha256: str
    content_sha256: str
    runtime_mode: str = "shared_reference"

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "publicationId": self.publication_id,
            "boundaryId": self.identity.boundary_id,
            "boundaryVersion": self.identity.version,
            "datasetId": self.dataset_id,
            "datasetVersion": self.dataset_version,
            "coordinateReference": {
                "coordinateReferenceId": self.coordinate_reference.coordinate_reference_id,
                "version": self.coordinate_reference.version,
                "authorityName": self.coordinate_reference.authority_name,
                "authorityCode": self.coordinate_reference.authority_code,
                "axisOrder": list(self.coordinate_reference.axis_order),
                "unit": self.coordinate_reference.unit,
            },
            "geometry": self.geometry,
            "extent": {
                "minLongitude": self.extent[0],
                "minLatitude": self.extent[1],
                "maxLongitude": self.extent[2],
                "maxLatitude": self.extent[3],
            },
            "sourceSha256": self.source_sha256,
            "contentSha256": self.content_sha256,
            "runtimeMode": self.runtime_mode,
        }
