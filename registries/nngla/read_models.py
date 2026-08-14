"""P006.7.9 deterministic, rebuildable NNGLA consumer read models."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Iterable

from .bundle15a_source import (
    load_administrative_areas,
    load_feature_name_assignments,
    load_feature_recognitions,
    load_places,
)
from .bundle15b_source import load_address_candidates, load_geometry_versions, load_road_candidates
from .bundle15c_source import load_parcel_bootstrap, load_state_land_bootstrap, load_title_bootstrap
from .publication_policy15d import (
    PublicReadDecision,
    decide_administrative_area_visibility,
    decide_feature_visibility,
    decide_place_visibility,
    decide_road_visibility,
)


def _semantic_checksum(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class NNGLAReadItem:
    subject_id: str
    family: str
    display_name: str
    lifecycle_status: str
    public_eligible: bool
    map_renderable: bool
    geometry_reference: str | None
    runtime_effect_scope: str
    visibility_reasons: tuple[str, ...]
    attributes: tuple[tuple[str, object], ...] = ()
    read_model_version: int = 1

    def __post_init__(self) -> None:
        if not self.subject_id or not self.family or not self.display_name:
            raise ValueError("read-model subject, family and display name are required")
        if self.read_model_version < 1:
            raise ValueError("read_model_version must be positive")
        if self.map_renderable and (not self.public_eligible or not self.geometry_reference):
            raise ValueError("map-renderable items must be public and have authoritative geometry")
        object.__setattr__(self, "attributes", tuple(sorted(tuple(self.attributes), key=lambda item: item[0])))

    def semantic_dict(self) -> dict[str, object]:
        return {
            "subjectId": self.subject_id,
            "family": self.family,
            "displayName": self.display_name,
            "lifecycleStatus": self.lifecycle_status,
            "publicEligible": self.public_eligible,
            "mapRenderable": self.map_renderable,
            "geometryReference": self.geometry_reference,
            "runtimeEffectScope": self.runtime_effect_scope,
            "visibilityReasons": list(self.visibility_reasons),
            "attributes": {k: v for k, v in self.attributes},
            "readModelVersion": self.read_model_version,
        }

    @property
    def checksum(self) -> str:
        return _semantic_checksum(self.semantic_dict())


@dataclass(frozen=True, slots=True)
class NNGLAReadFamilySummary:
    family: str
    source_count: int
    canonical_count: int
    published_count: int
    map_renderable_count: int
    population_state: str

    def __post_init__(self) -> None:
        if min(self.source_count, self.canonical_count, self.published_count, self.map_renderable_count) < 0:
            raise ValueError("read-family counts cannot be negative")
        if self.canonical_count > self.source_count or self.published_count > self.canonical_count or self.map_renderable_count > self.published_count:
            raise ValueError("read-family counts are inconsistent")


@dataclass(frozen=True, slots=True)
class NNGLAReadSnapshot:
    items: tuple[NNGLAReadItem, ...]
    summaries: tuple[NNGLAReadFamilySummary, ...]
    read_model_version: int = 1
    projected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.read_model_version < 1:
            raise ValueError("read_model_version must be positive")
        if self.projected_at.tzinfo is None or self.projected_at.utcoffset() is None:
            raise ValueError("projected_at must be timezone-aware")
        object.__setattr__(self, "projected_at", self.projected_at.astimezone(timezone.utc))
        object.__setattr__(self, "items", tuple(sorted(self.items, key=lambda item: (item.family, item.subject_id))))
        object.__setattr__(self, "summaries", tuple(sorted(self.summaries, key=lambda item: item.family)))

    @property
    def semantic_checksum(self) -> str:
        return _semantic_checksum({
            "readModelVersion": self.read_model_version,
            "items": [item.semantic_dict() for item in self.items],
            "summaries": [asdict(item) for item in self.summaries],
        })

    def public_items(self, family: str | None = None) -> tuple[NNGLAReadItem, ...]:
        return tuple(item for item in self.items if item.public_eligible and (family is None or item.family == family))

    def summary(self, family: str) -> NNGLAReadFamilySummary:
        for summary in self.summaries:
            if summary.family == family:
                return summary
        raise KeyError(f"unknown read-model family: {family}")


class MemoryNNGLAReadRepository:
    def __init__(self) -> None:
        self._snapshot: NNGLAReadSnapshot | None = None

    def replace(self, snapshot: NNGLAReadSnapshot) -> NNGLAReadSnapshot:
        if not isinstance(snapshot, NNGLAReadSnapshot):
            raise TypeError("snapshot must be NNGLAReadSnapshot")
        self._snapshot = snapshot
        return snapshot

    def get(self) -> NNGLAReadSnapshot:
        if self._snapshot is None:
            raise KeyError("NNGLA read snapshot has not been projected")
        return self._snapshot


class NNGLAReadProjector:
    FAMILY_PLACE = "PLACE"
    FAMILY_ADMIN = "ADMINISTRATIVE_AREA"
    FAMILY_FEATURE = "GEOGRAPHIC_FEATURE"
    FAMILY_ROAD = "ROAD"
    FAMILY_ADDRESS = "ADDRESS"
    FAMILY_PARCEL = "PARCEL"
    FAMILY_TITLE = "TITLE"
    FAMILY_STATE_LAND = "STATE_LAND"

    def _place_items(self) -> tuple[NNGLAReadItem, ...]:
        result = []
        for place in load_places():
            decision = decide_place_visibility(
                naming_status_code=place.naming_status_code,
                spatial_assignment_status=place.spatial_assignment_status,
            )
            result.append(NNGLAReadItem(
                subject_id=place.source_place_code,
                family=self.FAMILY_PLACE,
                display_name=place.canonical_name,
                lifecycle_status=place.lifecycle_status.value,
                public_eligible=decision.public_eligible,
                map_renderable=decision.map_renderable,
                geometry_reference=None,
                runtime_effect_scope=place.runtime_effect_scope.value,
                visibility_reasons=decision.reasons,
                attributes=(("placeType", place.place_type_code), ("regionCode", place.region_code), ("spatialAssignmentStatus", place.spatial_assignment_status)),
            ))
        return tuple(result)

    def _admin_items(self) -> tuple[NNGLAReadItem, ...]:
        result = []
        for area in load_administrative_areas():
            decision = decide_administrative_area_visibility(
                lifecycle_status=area.lifecycle_status.value,
                boundary_status=area.boundary_status,
                geometry_reference=area.geometry_reference,
            )
            result.append(NNGLAReadItem(
                subject_id=area.administrative_candidate_id,
                family=self.FAMILY_ADMIN,
                display_name=area.canonical_name,
                lifecycle_status=area.lifecycle_status.value,
                public_eligible=decision.public_eligible,
                map_renderable=decision.map_renderable,
                geometry_reference=area.geometry_reference,
                runtime_effect_scope=area.runtime_effect_scope.value,
                visibility_reasons=decision.reasons,
                attributes=(("administrativeType", area.administrative_type_code), ("boundaryStatus", area.boundary_status), ("regionCode", area.region_code)),
            ))
        return tuple(result)

    def _feature_items(self) -> tuple[NNGLAReadItem, ...]:
        assignments = {item.subject_id: item for item in load_feature_name_assignments() if item.role.value == "PRIMARY"}
        geometry = {item.subject_id: item for item in load_geometry_versions()}
        result = []
        for feature in load_feature_recognitions():
            assignment = assignments.get(feature.source_feature_id)
            geom = geometry.get(feature.source_feature_id)
            naming_status = "PROPOSED" if assignment is not None and assignment.assignment_status == "PROPOSED_UNGAZETTED" else None
            publication_status = geom.publication_status.value if geom else None
            decision = decide_feature_visibility(naming_status_code=naming_status, publication_status=publication_status)
            display_name = assignment.canonical_name if assignment else feature.source_feature_id
            result.append(NNGLAReadItem(
                subject_id=feature.recognition_id,
                family=self.FAMILY_FEATURE,
                display_name=display_name,
                lifecycle_status=feature.lifecycle_status.value,
                public_eligible=decision.public_eligible,
                map_renderable=decision.map_renderable,
                geometry_reference=geom.geometry_id if geom and decision.map_renderable else None,
                runtime_effect_scope=feature.runtime_effect_scope.value,
                visibility_reasons=decision.reasons,
                attributes=(("featureType", feature.feature_type_code), ("recognitionStatus", feature.recognition_status), ("sourceFeatureId", feature.source_feature_id)),
            ))
        return tuple(result)

    def _road_items(self) -> tuple[NNGLAReadItem, ...]:
        result = []
        for road in load_road_candidates():
            decision = decide_road_visibility(
                planning_status=road.planning_status,
                geometry_status=road.geometry_status,
                geometry_reference=road.geometry_reference,
            )
            result.append(NNGLAReadItem(
                subject_id=road.road_candidate_id,
                family=self.FAMILY_ROAD,
                display_name=road.canonical_name,
                lifecycle_status=road.planning_status,
                public_eligible=decision.public_eligible,
                map_renderable=decision.map_renderable,
                geometry_reference=road.geometry_reference,
                runtime_effect_scope=road.runtime_effect_scope.value,
                visibility_reasons=decision.reasons,
                attributes=(("roadClass", road.road_class_code), ("geometryStatus", road.geometry_status), ("roadNameId", road.road_name_id)),
            ))
        return tuple(result)

    def project(self, *, read_model_version: int = 1, projected_at: datetime | None = None) -> NNGLAReadSnapshot:
        if read_model_version < 1:
            raise ValueError("read_model_version must be positive")
        items = self._place_items() + self._admin_items() + self._feature_items() + self._road_items()
        source_counts = {
            self.FAMILY_PLACE: len(load_places()),
            self.FAMILY_ADMIN: len(load_administrative_areas()),
            self.FAMILY_FEATURE: len(load_feature_recognitions()),
            self.FAMILY_ROAD: len(load_road_candidates()),
            self.FAMILY_ADDRESS: len(load_address_candidates()),
            self.FAMILY_PARCEL: len(load_parcel_bootstrap()),
            self.FAMILY_TITLE: len(load_title_bootstrap()),
            self.FAMILY_STATE_LAND: len(load_state_land_bootstrap()),
        }
        # P006.7.9 is still pre-migration. These source-backed projections describe
        # governed repository evidence only; they must not masquerade as rows that
        # already exist in PostgreSQL. A later database adapter will populate the
        # canonical dimension without changing this public contract.
        canonical_counts = {family: 0 for family in source_counts}
        summaries = []
        for family in (self.FAMILY_PLACE, self.FAMILY_ADMIN, self.FAMILY_FEATURE, self.FAMILY_ROAD, self.FAMILY_ADDRESS, self.FAMILY_PARCEL, self.FAMILY_TITLE, self.FAMILY_STATE_LAND):
            family_items = tuple(item for item in items if item.family == family)
            source_count = source_counts[family]
            canonical_count = canonical_counts[family]
            published_count = sum(item.public_eligible for item in family_items)
            map_count = sum(item.map_renderable for item in family_items)
            if source_count == 0:
                population = "EMPTY_DAY_ZERO"
            elif canonical_count == 0:
                population = "SOURCE_READY_NOT_MIGRATED"
            elif published_count == 0:
                population = "CANONICAL_NOT_PUBLISHED"
            else:
                population = "PUBLICATION_AVAILABLE"
            summaries.append(NNGLAReadFamilySummary(family, source_count, canonical_count, published_count, map_count, population))
        return NNGLAReadSnapshot(tuple(items), tuple(summaries), read_model_version, projected_at or datetime.now(timezone.utc))

    def rebuild(self, repository: MemoryNNGLAReadRepository, *, read_model_version: int = 1) -> NNGLAReadSnapshot:
        return repository.replace(self.project(read_model_version=read_model_version))


__all__ = [
    "NNGLAReadItem", "NNGLAReadFamilySummary", "NNGLAReadSnapshot",
    "MemoryNNGLAReadRepository", "NNGLAReadProjector",
]
