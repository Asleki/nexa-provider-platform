"""P006.7.9 server-side NNGLA read service for public consumers."""
from __future__ import annotations
from .read_models import MemoryNNGLAReadRepository, NNGLAReadProjector, NNGLAReadSnapshot


class NNGLAReadService:
    PUBLIC_FAMILIES = frozenset({"PLACE", "ADMINISTRATIVE_AREA", "GEOGRAPHIC_FEATURE", "ROAD", "ADDRESS", "PARCEL"})

    def __init__(self, repository: MemoryNNGLAReadRepository | None = None, projector: NNGLAReadProjector | None = None) -> None:
        self.repository = repository or MemoryNNGLAReadRepository()
        self.projector = projector or NNGLAReadProjector()
        try:
            self.repository.get()
        except KeyError:
            self.projector.rebuild(self.repository)

    @property
    def snapshot(self) -> NNGLAReadSnapshot:
        return self.repository.get()

    def status_dict(self) -> dict[str, object]:
        snapshot = self.snapshot
        return {
            "authorityId": "authority:nngla",
            "countryId": "country:novegeo",
            "status": "READY",
            "readModelVersion": snapshot.read_model_version,
            "semanticChecksum": snapshot.semantic_checksum,
            "families": [
                {
                    "family": item.family,
                    "sourceCount": item.source_count,
                    "canonicalCount": item.canonical_count,
                    "publishedCount": item.published_count,
                    "mapRenderableCount": item.map_renderable_count,
                    "populationState": item.population_state,
                }
                for item in snapshot.summaries
            ],
            "privacyBoundary": "PUBLIC_READ_MODELS_ONLY",
            "databaseAuthority": "SERVER_SIDE_ONLY",
            "liveDatabaseMigrationStatus": "NOT_EXECUTED",
        }

    def list_public(self, family: str) -> dict[str, object]:
        normalized = str(family).strip().upper()
        if normalized not in self.PUBLIC_FAMILIES:
            raise KeyError(f"unsupported public NNGLA family: {family}")
        items = self.snapshot.public_items(normalized)
        summary = self.snapshot.summary(normalized)
        return {
            "family": normalized,
            "items": [item.semantic_dict() for item in items],
            "count": len(items),
            "sourceCount": summary.source_count,
            "canonicalCount": summary.canonical_count,
            "publishedCount": summary.published_count,
            "mapRenderableCount": summary.map_renderable_count,
            "populationState": summary.population_state,
            "readModelVersion": self.snapshot.read_model_version,
            "semanticChecksum": self.snapshot.semantic_checksum,
        }


__all__ = ["NNGLAReadService"]
