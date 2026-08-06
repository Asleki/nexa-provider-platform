"""Deterministic geography-specific qualification for world-boundary candidates."""
from __future__ import annotations

from dataclasses import dataclass

from .contracts import WorldBoundaryCandidate
from .geometry import boundary_extent, canonical_sha256, normalize_boundary_geometry


@dataclass(frozen=True, slots=True)
class WorldBoundaryQualificationReceipt:
    qualification_id: str
    boundary_id: str
    boundary_version: int
    decision: str
    normalized_geometry: dict
    extent: tuple[float, float, float, float]
    source_sha256: str
    content_sha256: str


class WorldBoundaryQualificationService:
    def qualify(self, candidate: WorldBoundaryCandidate, *, qualification_id: str) -> WorldBoundaryQualificationReceipt:
        normalized = normalize_boundary_geometry(candidate.geometry)
        source_sha256 = canonical_sha256(candidate.geometry)
        content = {
            "boundaryId": candidate.identity.boundary_id,
            "boundaryVersion": candidate.identity.version,
            "datasetId": candidate.dataset_id,
            "datasetVersion": candidate.dataset_version,
            "coordinateReferenceId": candidate.coordinate_reference.coordinate_reference_id,
            "coordinateReferenceVersion": candidate.coordinate_reference.version,
            "geometry": normalized,
        }
        return WorldBoundaryQualificationReceipt(
            qualification_id=qualification_id,
            boundary_id=candidate.identity.boundary_id,
            boundary_version=candidate.identity.version,
            decision="qualified",
            normalized_geometry=normalized,
            extent=boundary_extent(normalized),
            source_sha256=source_sha256,
            content_sha256=canonical_sha256(content),
        )
