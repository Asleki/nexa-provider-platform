"""P006.7.11.15.6.1 additive REGION metadata on the existing NNGLA map service."""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Iterable

from infrastructure.api.services.nngla_map_read_service import PostgreSQLNNGLAMapReadService
from infrastructure.database.read.nngla_region_public_map import (
    OFFICIAL_NOVEGEO_REGION_IDS,
    REGION_CLASSIFICATION_CODE,
    REGION_FAMILY,
    PostgreSQLRegionPublicMapRepository,
)

REGION_MAP_INTEGRATION_VERSION = 1
_OFFICIAL_REGION_SET = frozenset(OFFICIAL_NOVEGEO_REGION_IDS)


def _checksum(payload: object) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


class PostgreSQLRegionAugmentedNNGLAMapReadService(PostgreSQLNNGLAMapReadService):
    """Preserve the locked map service and add governed REGION presentation facts."""

    def __init__(self, repository, region_repository: PostgreSQLRegionPublicMapRepository) -> None:
        super().__init__(repository)
        if region_repository is None:
            raise TypeError("region_repository is required")
        if str(repository.runtime_mode) != str(region_repository.runtime_mode):
            raise ValueError("repository and region_repository runtime modes must match")
        self.region_repository = region_repository

    def _enrich(self, items: Iterable[dict[str, object]]) -> list[dict[str, object]]:
        materialized = [dict(item) for item in items]
        region_ids = [
            str(item.get("subjectId"))
            for item in materialized
            if item.get("family") == REGION_FAMILY
            and str(item.get("classificationCode") or "").upper() == REGION_CLASSIFICATION_CODE
            and str(item.get("subjectId")) in _OFFICIAL_REGION_SET
        ]
        metadata = self.region_repository.metadata_for_subjects(region_ids)
        enriched: list[dict[str, object]] = []
        for item in materialized:
            subject_id = str(item.get("subjectId"))
            if subject_id in metadata:
                item.update(metadata[subject_id].as_public_fields())
            enriched.append(item)
        return enriched

    def list_features(self, **kwargs) -> dict[str, object]:
        body = dict(super().list_features(**kwargs))
        items = self._enrich(body.get("items", []))
        body["items"] = items
        body["count"] = len(items)
        body["regionMapIntegrationVersion"] = REGION_MAP_INTEGRATION_VERSION
        bounds = body.get("bounds") or {}
        semantic = {
            "runtime": body.get("readRuntime"),
            "bounds": [
                bounds.get("minLongitude"),
                bounds.get("minLatitude"),
                bounds.get("maxLongitude"),
                bounds.get("maxLatitude"),
            ],
            "families": list(body.get("families") or []),
            "items": items,
            "nextCursor": body.get("nextCursor"),
            "readModelVersion": body.get("mapReadModelVersion"),
            "regionMapIntegrationVersion": REGION_MAP_INTEGRATION_VERSION,
        }
        body["semanticChecksum"] = _checksum(semantic)
        return body

    def get_subject(self, subject_id: str) -> dict[str, object] | None:
        body = super().get_subject(subject_id)
        if body is None:
            return None
        result = dict(body)
        item = self._enrich([dict(result["item"])])[0]
        result["item"] = item
        result["regionMapIntegrationVersion"] = REGION_MAP_INTEGRATION_VERSION
        result["semanticChecksum"] = _checksum(
            {
                "runtime": result.get("readRuntime"),
                "item": item,
                "regionMapIntegrationVersion": REGION_MAP_INTEGRATION_VERSION,
            }
        )
        return result


__all__ = [
    "REGION_MAP_INTEGRATION_VERSION",
    "PostgreSQLRegionAugmentedNNGLAMapReadService",
]
