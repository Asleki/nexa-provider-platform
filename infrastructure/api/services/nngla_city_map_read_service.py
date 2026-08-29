"""P006.7.11.15.7.2 additive CITY metadata on the existing NNGLA map service."""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Iterable

from infrastructure.api.services.nngla_region_map_read_service import (
    PostgreSQLRegionAugmentedNNGLAMapReadService,
)
from infrastructure.database.read.nngla_city_public_map import (
    CITY_CLASSIFICATION_CODE,
    CITY_FAMILY,
    OFFICIAL_NOVEGEO_CITY_IDS,
    PostgreSQLCityPublicMapRepository,
)

CITY_MAP_INTEGRATION_VERSION = 1
_OFFICIAL_CITY_SET = frozenset(OFFICIAL_NOVEGEO_CITY_IDS)


def _checksum(payload: object) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


class PostgreSQLCityAugmentedNNGLAMapReadService(PostgreSQLRegionAugmentedNNGLAMapReadService):
    """Preserve REGION enrichment and append governed CITY presentation facts."""

    def __init__(self, repository, region_repository, city_repository: PostgreSQLCityPublicMapRepository) -> None:
        super().__init__(repository, region_repository)
        if city_repository is None:
            raise TypeError("city_repository is required")
        if str(repository.runtime_mode) != str(city_repository.runtime_mode):
            raise ValueError("repository and CITY repository runtime modes must match")
        self.city_repository = city_repository

    def _enrich_city(self, items: Iterable[dict[str, object]]) -> list[dict[str, object]]:
        materialized = [dict(item) for item in items]
        city_ids = [
            str(item.get("subjectId"))
            for item in materialized
            if item.get("family") == CITY_FAMILY
            and str(item.get("classificationCode") or "").upper() == CITY_CLASSIFICATION_CODE
            and str(item.get("subjectId")) in _OFFICIAL_CITY_SET
        ]
        metadata = self.city_repository.metadata_for_subjects(city_ids)
        enriched: list[dict[str, object]] = []
        for item in materialized:
            subject_id = str(item.get("subjectId"))
            if subject_id in metadata:
                item.update(metadata[subject_id].as_public_fields())
            enriched.append(item)
        return enriched

    def list_features(self, **kwargs) -> dict[str, object]:
        body = dict(super().list_features(**kwargs))
        items = self._enrich_city(body.get("items", []))
        body["items"] = items
        body["count"] = len(items)
        body["cityMapIntegrationVersion"] = CITY_MAP_INTEGRATION_VERSION
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
            "regionMapIntegrationVersion": body.get("regionMapIntegrationVersion"),
            "cityMapIntegrationVersion": CITY_MAP_INTEGRATION_VERSION,
        }
        body["semanticChecksum"] = _checksum(semantic)
        return body

    def get_subject(self, subject_id: str) -> dict[str, object] | None:
        body = super().get_subject(subject_id)
        if body is None:
            return None
        result = dict(body)
        item = self._enrich_city([dict(result["item"])])[0]
        result["item"] = item
        result["cityMapIntegrationVersion"] = CITY_MAP_INTEGRATION_VERSION
        result["semanticChecksum"] = _checksum(
            {
                "runtime": result.get("readRuntime"),
                "item": item,
                "regionMapIntegrationVersion": result.get("regionMapIntegrationVersion"),
                "cityMapIntegrationVersion": CITY_MAP_INTEGRATION_VERSION,
            }
        )
        return result


__all__ = [
    "CITY_MAP_INTEGRATION_VERSION",
    "PostgreSQLCityAugmentedNNGLAMapReadService",
]
