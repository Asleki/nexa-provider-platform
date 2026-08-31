"""Additive MUNICIPALITY metadata over the locked REGION/CITY map service."""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Iterable

from infrastructure.api.services.nngla_city_map_read_service import (
    PostgreSQLCityAugmentedNNGLAMapReadService,
)
from infrastructure.database.read.nngla_municipality_public_map import (
    MUNICIPALITY_CLASSIFICATION_CODE,
    MUNICIPALITY_FAMILY,
    PostgreSQLMunicipalityPublicMapRepository,
)

MUNICIPALITY_MAP_INTEGRATION_VERSION = 1


def _checksum(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


class PostgreSQLMunicipalityAugmentedNNGLAMapReadService(
    PostgreSQLCityAugmentedNNGLAMapReadService
):
    """Preserve REGION/CITY enrichment and append governed MUNICIPALITY facts."""

    def __init__(
        self,
        repository,
        region_repository,
        city_repository,
        municipality_repository: PostgreSQLMunicipalityPublicMapRepository,
    ) -> None:
        super().__init__(repository, region_repository, city_repository)
        if municipality_repository is None:
            raise TypeError("municipality_repository is required")
        if str(repository.runtime_mode) != str(municipality_repository.runtime_mode):
            raise ValueError("repository and MUNICIPALITY repository runtime modes must match")
        self.municipality_repository = municipality_repository

    def _enrich_municipality(
        self,
        items: Iterable[dict[str, object]],
    ) -> list[dict[str, object]]:
        materialized = [dict(item) for item in items]
        municipality_ids = [
            str(item.get("subjectId"))
            for item in materialized
            if item.get("family") == MUNICIPALITY_FAMILY
            and str(item.get("classificationCode") or "").upper()
                == MUNICIPALITY_CLASSIFICATION_CODE
        ]
        metadata = self.municipality_repository.metadata_for_subjects(municipality_ids)
        enriched = []
        for item in materialized:
            subject_id = str(item.get("subjectId"))
            if subject_id in metadata:
                item.update(metadata[subject_id].as_public_fields())
            enriched.append(item)
        return enriched

    def list_features(self, **kwargs) -> dict[str, object]:
        body = dict(super().list_features(**kwargs))
        items = self._enrich_municipality(body.get("items", []))
        body["items"] = items
        body["count"] = len(items)
        body["municipalityMapIntegrationVersion"] = MUNICIPALITY_MAP_INTEGRATION_VERSION
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
            "cityMapIntegrationVersion": body.get("cityMapIntegrationVersion"),
            "municipalityMapIntegrationVersion": MUNICIPALITY_MAP_INTEGRATION_VERSION,
        }
        body["semanticChecksum"] = _checksum(semantic)
        return body

    def get_subject(self, subject_id: str) -> dict[str, object] | None:
        body = super().get_subject(subject_id)
        if body is None:
            return None
        result = dict(body)
        item = self._enrich_municipality([dict(result["item"])])[0]
        result["item"] = item
        result["municipalityMapIntegrationVersion"] = MUNICIPALITY_MAP_INTEGRATION_VERSION
        result["semanticChecksum"] = _checksum(
            {
                "runtime": result.get("readRuntime"),
                "item": item,
                "regionMapIntegrationVersion": result.get("regionMapIntegrationVersion"),
                "cityMapIntegrationVersion": result.get("cityMapIntegrationVersion"),
                "municipalityMapIntegrationVersion": MUNICIPALITY_MAP_INTEGRATION_VERSION,
            }
        )
        return result


__all__ = [
    "MUNICIPALITY_MAP_INTEGRATION_VERSION",
    "PostgreSQLMunicipalityAugmentedNNGLAMapReadService",
]
