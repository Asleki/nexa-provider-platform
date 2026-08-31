"""P006.7.11.15.9.3 additive TOWN metadata over CITY_DISTRICT map reads."""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Iterable

from infrastructure.api.services.nngla_city_district_map_read_service import (
    PostgreSQLCityDistrictAugmentedNNGLAMapReadService,
)
from infrastructure.database.read.nngla_town_public_map import (
    TOWN_CLASSIFICATION_CODE,
    TOWN_FAMILY,
    PostgreSQLTownPublicMapRepository,
)

TOWN_MAP_INTEGRATION_VERSION = 1


def _checksum(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


class PostgreSQLTownAugmentedNNGLAMapReadService(
    PostgreSQLCityDistrictAugmentedNNGLAMapReadService
):
    """Preserve prior governed enrichment and append TOWN footprint facts."""

    def __init__(
        self,
        repository,
        region_repository,
        city_repository,
        municipality_repository,
        city_district_repository,
        town_repository: PostgreSQLTownPublicMapRepository,
    ) -> None:
        super().__init__(
            repository,
            region_repository,
            city_repository,
            municipality_repository,
            city_district_repository,
        )
        if town_repository is None:
            raise TypeError("town_repository is required")
        if str(repository.runtime_mode) != str(town_repository.runtime_mode):
            raise ValueError("repository and TOWN repository runtime modes must match")
        self.town_repository = town_repository

    def _enrich_town(
        self,
        items: Iterable[dict[str, object]],
    ) -> list[dict[str, object]]:
        materialized = [dict(item) for item in items]
        town_ids = [
            str(item.get("subjectId"))
            for item in materialized
            if item.get("family") == TOWN_FAMILY
            and str(item.get("classificationCode") or "").upper()
            == TOWN_CLASSIFICATION_CODE
        ]
        metadata = self.town_repository.metadata_for_subjects(town_ids)
        enriched: list[dict[str, object]] = []
        for item in materialized:
            subject_id = str(item.get("subjectId"))
            if subject_id in metadata:
                item.update(metadata[subject_id].as_public_fields())
            enriched.append(item)
        return enriched

    def list_features(self, **kwargs) -> dict[str, object]:
        body = dict(super().list_features(**kwargs))
        items = self._enrich_town(body.get("items", []))
        body["items"] = items
        body["count"] = len(items)
        body["townMapIntegrationVersion"] = TOWN_MAP_INTEGRATION_VERSION
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
            "municipalityMapIntegrationVersion": body.get(
                "municipalityMapIntegrationVersion"
            ),
            "cityDistrictMapIntegrationVersion": body.get(
                "cityDistrictMapIntegrationVersion"
            ),
            "townMapIntegrationVersion": TOWN_MAP_INTEGRATION_VERSION,
        }
        body["semanticChecksum"] = _checksum(semantic)
        return body

    def get_subject(self, subject_id: str) -> dict[str, object] | None:
        body = super().get_subject(subject_id)
        if body is None:
            return None
        result = dict(body)
        item = self._enrich_town([dict(result["item"])])[0]
        result["item"] = item
        result["townMapIntegrationVersion"] = TOWN_MAP_INTEGRATION_VERSION
        result["semanticChecksum"] = _checksum(
            {
                "runtime": result.get("readRuntime"),
                "item": item,
                "regionMapIntegrationVersion": result.get(
                    "regionMapIntegrationVersion"
                ),
                "cityMapIntegrationVersion": result.get(
                    "cityMapIntegrationVersion"
                ),
                "municipalityMapIntegrationVersion": result.get(
                    "municipalityMapIntegrationVersion"
                ),
                "cityDistrictMapIntegrationVersion": result.get(
                    "cityDistrictMapIntegrationVersion"
                ),
                "townMapIntegrationVersion": TOWN_MAP_INTEGRATION_VERSION,
            }
        )
        return result


__all__ = [
    "TOWN_MAP_INTEGRATION_VERSION",
    "PostgreSQLTownAugmentedNNGLAMapReadService",
]
