"""Live PostgreSQL-backed NNGLA public read service for P006.7.11.8."""
from __future__ import annotations

from hashlib import sha256
import json

from infrastructure.database.read.nngla import PostgreSQLNNGLAReadRepository, PUBLIC_FAMILIES


def _checksum(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def _population_state(source: int, canonical: int, published: int) -> str:
    if source == 0 and canonical == 0:
        return "EMPTY_DAY_ZERO"
    if canonical == 0:
        return "SOURCE_READY_NOT_CANONICAL"
    if published == 0:
        return "CANONICAL_NOT_PUBLISHED"
    return "PUBLISHED"


class PostgreSQLNNGLAReadService:
    """Formats live PostgreSQL truth behind the existing GET-only NNGLA routes."""

    PUBLIC_FAMILIES = frozenset(PUBLIC_FAMILIES)

    def __init__(self, repository: PostgreSQLNNGLAReadRepository) -> None:
        if repository is None:
            raise TypeError("repository is required")
        self.repository = repository

    def status_dict(self) -> dict[str, object]:
        counts = self.repository.family_counts()
        read_model_version = self.repository.read_model_version()
        migration_status = self.repository.coordinate_migration_status()
        families = [
            {
                "family": family,
                "sourceCount": counts[family].source_count,
                "canonicalCount": counts[family].canonical_count,
                "publishedCount": counts[family].published_count,
                "mapRenderableCount": counts[family].map_renderable_count,
                "populationState": _population_state(
                    counts[family].source_count,
                    counts[family].canonical_count,
                    counts[family].published_count,
                ),
            }
            for family in PUBLIC_FAMILIES
        ]
        semantic = {
            "readModelVersion": read_model_version,
            "runtimeMode": self.repository.runtime_mode,
            "liveDatabaseMigrationStatus": migration_status,
            "families": families,
        }
        return {
            "authorityId": "authority:nngla",
            "countryId": "country:novegeo",
            "status": "READY" if migration_status == "EXECUTED" else "DEGRADED",
            "readRuntime": self.repository.runtime_mode,
            "readModelVersion": read_model_version,
            "semanticChecksum": _checksum(semantic),
            "families": families,
            "privacyBoundary": "PUBLIC_READ_MODELS_ONLY",
            "databaseAuthority": "SERVER_SIDE_ONLY",
            "liveDatabaseMigrationStatus": migration_status,
        }

    def list_public(self, family: str) -> dict[str, object]:
        normalized = str(family).strip().upper()
        if normalized not in self.PUBLIC_FAMILIES:
            raise KeyError(f"unsupported public NNGLA family: {family}")
        counts = self.repository.family_counts()[normalized]
        items = self.repository.public_items(normalized)
        read_model_version = self.repository.read_model_version()
        semantic = {
            "family": normalized,
            "runtimeMode": self.repository.runtime_mode,
            "readModelVersion": read_model_version,
            "items": items,
            "counts": {
                "source": counts.source_count,
                "canonical": counts.canonical_count,
                "published": counts.published_count,
                "map": counts.map_renderable_count,
            },
        }
        return {
            "family": normalized,
            "items": list(items),
            "count": len(items),
            "sourceCount": counts.source_count,
            "canonicalCount": counts.canonical_count,
            "publishedCount": counts.published_count,
            "mapRenderableCount": counts.map_renderable_count,
            "populationState": _population_state(counts.source_count, counts.canonical_count, counts.published_count),
            "readRuntime": self.repository.runtime_mode,
            "readModelVersion": read_model_version,
            "semanticChecksum": _checksum(semantic),
        }


__all__ = ["PostgreSQLNNGLAReadService"]
