"""P006.7.11.15.9 sequence-29 TOWN map-service successor.

TOWN authority is its published MUNICIPALITY.  The service decorates the map
service already present in the extension context; CITY_DISTRICT is optional and
is never an authority/runtime prerequisite for TOWN publication or reads.
"""
from __future__ import annotations

from copy import copy
from hashlib import sha256
import json
from typing import Iterable

from infrastructure.api.services.nngla_municipality_map_read_service import (
    PostgreSQLMunicipalityAugmentedNNGLAMapReadService,
)
from infrastructure.api.services.nngla_city_district_map_read_service import (
    PostgreSQLCityDistrictAugmentedNNGLAMapReadService,
)
from infrastructure.database.read.nngla_town_public_map import (
    TOWN_CLASSIFICATION_CODE,
    TOWN_FAMILY,
    PostgreSQLTownPublicMapRepository,
)

TOWN_MAP_INTEGRATION_VERSION = 2


def _checksum(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def _rebind_service(service, repository):
    rebound = copy(service)
    if not hasattr(rebound, "repository"):
        raise TypeError("base map service must expose repository")
    rebound.repository = repository
    if hasattr(rebound, "base_service"):
        rebound.base_service = _rebind_service(rebound.base_service, repository)
    return rebound


def _integration_versions(body: dict[str, object]) -> dict[str, object]:
    return {
        key: body[key]
        for key in sorted(body)
        if key.endswith("MapIntegrationVersion")
    }


class PostgreSQLTownAugmentedNNGLAMapReadService:
    """Decorate the current map service with governed TOWN presentation facts."""

    def __init__(self, repository, *args) -> None:
        # Sequence-29 runtime signature: (repository, base_service, town_repo).
        # Preserve the historical 6-argument constructor for compatibility only.
        if len(args) == 2:
            base_service, town_repository = args
        elif len(args) == 5:
            region_repository, city_repository, municipality_repository, city_district_repository, town_repository = args
            municipality_service = PostgreSQLMunicipalityAugmentedNNGLAMapReadService(
                repository, region_repository, city_repository, municipality_repository
            )
            base_service = PostgreSQLCityDistrictAugmentedNNGLAMapReadService(
                repository, municipality_service, city_district_repository
            )
        else:
            raise TypeError("expected base_service+town_repository or historical compatibility arguments")
        if repository is None or base_service is None or town_repository is None:
            raise TypeError("repository, base_service and town_repository are required")
        if str(repository.runtime_mode) != str(town_repository.runtime_mode):
            raise ValueError("repository and TOWN repository runtime modes must match")
        self.repository = repository
        self.base_service = _rebind_service(base_service, repository)
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
        body = dict(self.base_service.list_features(**kwargs))
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
            "integrationVersions": _integration_versions(body),
        }
        body["semanticChecksum"] = _checksum(semantic)
        return body

    def get_subject(self, subject_id: str) -> dict[str, object] | None:
        body = self.base_service.get_subject(subject_id)
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
                "integrationVersions": _integration_versions(result),
            }
        )
        return result


__all__ = [
    "TOWN_MAP_INTEGRATION_VERSION",
    "PostgreSQLTownAugmentedNNGLAMapReadService",
]
