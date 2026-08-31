"""P006.7.11.15.9.2 additive CITY_DISTRICT metadata over MUNICIPALITY map reads."""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Iterable

from infrastructure.api.services.nngla_municipality_map_read_service import (
    PostgreSQLMunicipalityAugmentedNNGLAMapReadService,
)
from infrastructure.database.read.nngla_city_district_public_map import (
    CITY_DISTRICT_CLASSIFICATION_CODE,
    CITY_DISTRICT_FAMILY,
    PostgreSQLCityDistrictPublicMapRepository,
)

CITY_DISTRICT_MAP_INTEGRATION_VERSION = 1


def _checksum(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


class PostgreSQLCityDistrictAugmentedNNGLAMapReadService(
    PostgreSQLMunicipalityAugmentedNNGLAMapReadService
):
    """Preserve REGION/CITY/MUNICIPALITY enrichment and append CITY_DISTRICT facts."""

    def __init__(
        self,
        repository,
        region_repository,
        city_repository,
        municipality_repository,
        city_district_repository: PostgreSQLCityDistrictPublicMapRepository,
    ) -> None:
        super().__init__(
            repository,
            region_repository,
            city_repository,
            municipality_repository,
        )
        if city_district_repository is None:
            raise TypeError("city_district_repository is required")
        if str(repository.runtime_mode) != str(city_district_repository.runtime_mode):
            raise ValueError(
                "repository and CITY_DISTRICT repository runtime modes must match"
            )
        self.city_district_repository = city_district_repository

    def _enrich_city_district(
        self,
        items: Iterable[dict[str, object]],
    ) -> list[dict[str, object]]:
        materialized = [dict(item) for item in items]
        district_ids = [
            str(item.get("subjectId"))
            for item in materialized
            if item.get("family") == CITY_DISTRICT_FAMILY
            and str(item.get("classificationCode") or "").upper()
            == CITY_DISTRICT_CLASSIFICATION_CODE
        ]
        metadata = self.city_district_repository.metadata_for_subjects(district_ids)
        enriched: list[dict[str, object]] = []
        for item in materialized:
            subject_id = str(item.get("subjectId"))
            if subject_id in metadata:
                item.update(metadata[subject_id].as_public_fields())
            enriched.append(item)
        return enriched

    def list_features(self, **kwargs) -> dict[str, object]:
        body = dict(super().list_features(**kwargs))
        items = self._enrich_city_district(body.get("items", []))
        body["items"] = items
        body["count"] = len(items)
        body["cityDistrictMapIntegrationVersion"] = (
            CITY_DISTRICT_MAP_INTEGRATION_VERSION
        )
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
            "cityDistrictMapIntegrationVersion": (
                CITY_DISTRICT_MAP_INTEGRATION_VERSION
            ),
        }
        body["semanticChecksum"] = _checksum(semantic)
        return body

    def get_subject(self, subject_id: str) -> dict[str, object] | None:
        body = super().get_subject(subject_id)
        if body is None:
            return None
        result = dict(body)
        item = self._enrich_city_district([dict(result["item"])])[0]
        result["item"] = item
        result["cityDistrictMapIntegrationVersion"] = (
            CITY_DISTRICT_MAP_INTEGRATION_VERSION
        )
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
                "cityDistrictMapIntegrationVersion": (
                    CITY_DISTRICT_MAP_INTEGRATION_VERSION
                ),
            }
        )
        return result


__all__ = [
    "CITY_DISTRICT_MAP_INTEGRATION_VERSION",
    "PostgreSQLCityDistrictAugmentedNNGLAMapReadService",
]
