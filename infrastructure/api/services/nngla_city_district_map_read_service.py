"""P006.7.11.15.9 sequence-29 CITY_DISTRICT map-service successor.

CITY_DISTRICT authority is its published CITY.  This service decorates whatever
map service already exists in the additive extension context, so MUNICIPALITY
metadata is preserved when present but is never a runtime dependency.
"""
from __future__ import annotations

from copy import copy
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

CITY_DISTRICT_MAP_INTEGRATION_VERSION = 2


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
    """Shallow-clone an existing additive service and bind it to a successor repo.

    Sequence-29 wrappers may themselves be nested.  Rebind the nested base
    service recursively so every read in the chain sees the same augmented map
    repository while preserving all earlier REGION/CITY/MUNICIPALITY metadata.
    """
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


class PostgreSQLCityDistrictAugmentedNNGLAMapReadService:
    """Decorate the current map service with CITY_DISTRICT presentation facts."""

    def __init__(self, repository, *args) -> None:
        # Sequence-29 runtime signature: (repository, base_service, district_repo).
        # The historical 5-argument signature remains accepted for source/test
        # compatibility, but is not used by extension composition.
        if len(args) == 2:
            base_service, city_district_repository = args
        elif len(args) == 4:
            region_repository, city_repository, municipality_repository, city_district_repository = args
            base_service = PostgreSQLMunicipalityAugmentedNNGLAMapReadService(
                repository, region_repository, city_repository, municipality_repository
            )
        else:
            raise TypeError("expected base_service+district_repository or historical compatibility arguments")
        if repository is None or base_service is None or city_district_repository is None:
            raise TypeError("repository, base_service and city_district_repository are required")
        if str(repository.runtime_mode) != str(city_district_repository.runtime_mode):
            raise ValueError(
                "repository and CITY_DISTRICT repository runtime modes must match"
            )
        self.repository = repository
        self.base_service = _rebind_service(base_service, repository)
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
        body = dict(self.base_service.list_features(**kwargs))
        items = self._enrich_city_district(body.get("items", []))
        body["items"] = items
        body["count"] = len(items)
        body["cityDistrictMapIntegrationVersion"] = CITY_DISTRICT_MAP_INTEGRATION_VERSION
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
        item = self._enrich_city_district([dict(result["item"])])[0]
        result["item"] = item
        result["cityDistrictMapIntegrationVersion"] = CITY_DISTRICT_MAP_INTEGRATION_VERSION
        result["semanticChecksum"] = _checksum(
            {
                "runtime": result.get("readRuntime"),
                "item": item,
                "integrationVersions": _integration_versions(result),
            }
        )
        return result


__all__ = [
    "CITY_DISTRICT_MAP_INTEGRATION_VERSION",
    "PostgreSQLCityDistrictAugmentedNNGLAMapReadService",
]
