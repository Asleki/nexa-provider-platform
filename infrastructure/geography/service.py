"""Application service for the active governed NoveGeo world geometry."""
from __future__ import annotations

import json
from pathlib import Path

from .contracts import BoundaryIdentity, CoordinateReference, WorldBoundaryCandidate, WorldBoundaryPublication
from .qualification import WorldBoundaryQualificationService
from .repository import InMemoryWorldBoundaryRepository, WorldBoundaryRepository


class WorldGeometryNotFound(LookupError):
    pass


class WorldGeometryService:
    def __init__(self, repository: WorldBoundaryRepository) -> None:
        self.repository = repository

    def publish_candidate(self, candidate: WorldBoundaryCandidate, *, publication_id: str, qualification_id: str) -> WorldBoundaryPublication:
        receipt = WorldBoundaryQualificationService().qualify(candidate, qualification_id=qualification_id)
        publication = WorldBoundaryPublication(
            publication_id=publication_id,
            identity=candidate.identity,
            dataset_id=candidate.dataset_id,
            dataset_version=candidate.dataset_version,
            coordinate_reference=candidate.coordinate_reference,
            geometry=receipt.normalized_geometry,
            extent=receipt.extent,
            source_sha256=receipt.source_sha256,
            content_sha256=receipt.content_sha256,
            runtime_mode=candidate.runtime_mode,
        )
        self.repository.save(publication)
        return publication

    def get_active(self) -> WorldBoundaryPublication:
        publication = self.repository.get_active()
        if publication is None:
            raise WorldGeometryNotFound("active NoveGeo world boundary is unavailable")
        return publication


def build_default_world_geometry_service() -> WorldGeometryService:
    repository = InMemoryWorldBoundaryRepository()
    source = Path(__file__).parents[2] / "data/novegeo/geography/world-boundary/qualified/novegeo_world_boundary_v001.geojson"
    if source.is_file():
        payload = json.loads(source.read_text(encoding="utf-8"))
        feature = payload["features"][0]
        candidate = WorldBoundaryCandidate(
            identity=BoundaryIdentity(feature["properties"]["boundaryId"], feature["properties"]["boundaryVersion"]),
            dataset_id=feature["properties"]["datasetId"],
            dataset_version=feature["properties"]["datasetVersion"],
            source_package_id=feature["properties"]["sourcePackageId"],
            coordinate_reference=CoordinateReference(),
            geometry=feature["geometry"],
        )
        WorldGeometryService(repository).publish_candidate(
            candidate,
            publication_id="publication:novegeo:world-boundary:v001",
            qualification_id="qualification:novegeo:world-boundary:v001",
        )
    return WorldGeometryService(repository)
