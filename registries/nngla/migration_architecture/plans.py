"""P006.7.11.4 reusable NNGLA migration-plan catalogue."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .selectors import Selector, SelectorKind
from .source_catalogue import SOURCE_DESCRIPTORS, SourceKind


class PlanPurpose(str, Enum):
    CANONICAL_OBJECT = "CANONICAL_OBJECT"
    REFERENCE_CATALOGUE = "REFERENCE_CATALOGUE"
    SOVEREIGN_AUTHORITY = "SOVEREIGN_AUTHORITY"


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    plan_id: str
    version: int
    source_key: str
    purpose: PlanPurpose
    qualification_profile: str
    selector: Selector
    runtime_mode: str = "production"
    effect_scope: str = "SHARED_REFERENCE"
    write_policy: str = "PREVIEW_ONLY"

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("plan version must be positive")
        if self.source_key not in SOURCE_DESCRIPTORS:
            raise ValueError(f"unknown source key: {self.source_key}")
        if self.runtime_mode not in {"simulation", "production"}:
            raise ValueError("invalid runtime_mode")
        if self.write_policy != "PREVIEW_ONLY":
            raise ValueError("Bundle 16B plans are zero-write PREVIEW_ONLY")
        descriptor = SOURCE_DESCRIPTORS[self.source_key]
        if self.purpose is PlanPurpose.REFERENCE_CATALOGUE and descriptor.kind is not SourceKind.REFERENCE_CATALOGUE:
            raise ValueError("reference plan must use reference catalogue source")
        if self.purpose is PlanPurpose.SOVEREIGN_AUTHORITY and descriptor.kind is not SourceKind.SOVEREIGN_AUTHORITY:
            raise ValueError("sovereign plan must use sovereign authority source")
        if self.purpose is PlanPurpose.CANONICAL_OBJECT and descriptor.kind is SourceKind.REFERENCE_CATALOGUE:
            raise ValueError("reference catalogue cannot be promoted by canonical-object plan")

    def with_selector(self, selector: Selector) -> "MigrationPlan":
        return replace(self, selector=selector)


PLAN_CATALOGUE: dict[str, MigrationPlan] = {
    "sovereign-boundary": MigrationPlan(
        "sovereign-boundary", 1, "sovereign-boundary", PlanPurpose.SOVEREIGN_AUTHORITY,
        "sovereign-boundary-v1", Selector(),
    ),
    "places": MigrationPlan("places", 1, "places", PlanPurpose.CANONICAL_OBJECT, "place-v1", Selector()),
    "places:city": MigrationPlan(
        "places:city", 1, "places", PlanPurpose.CANONICAL_OBJECT, "place-v1",
        Selector(SelectorKind.FIELD_EQUALS, "place_type_code", ("CITY",)),
    ),
    "places:municipality": MigrationPlan(
        "places:municipality", 1, "places", PlanPurpose.CANONICAL_OBJECT, "place-v1",
        Selector(SelectorKind.FIELD_EQUALS, "place_type_code", ("MUNICIPALITY",)),
    ),
    "places:town": MigrationPlan(
        "places:town", 1, "places", PlanPurpose.CANONICAL_OBJECT, "place-v1",
        Selector(SelectorKind.FIELD_EQUALS, "place_type_code", ("TOWN",)),
    ),
    "places:village": MigrationPlan(
        "places:village", 1, "places", PlanPurpose.CANONICAL_OBJECT, "place-v1",
        Selector(SelectorKind.FIELD_EQUALS, "place_type_code", ("VILLAGE",)),
    ),
    "administrative-areas": MigrationPlan(
        "administrative-areas", 1, "administrative-areas", PlanPurpose.CANONICAL_OBJECT,
        "administrative-area-v1", Selector(),
    ),
    "roads": MigrationPlan("roads", 1, "roads", PlanPurpose.CANONICAL_OBJECT, "road-v1", Selector()),
    "geographic-features": MigrationPlan(
        "geographic-features", 1, "geographic-features", PlanPurpose.CANONICAL_OBJECT,
        "geographic-feature-v1", Selector(),
    ),
    "geometry": MigrationPlan("geometry", 1, "geometry", PlanPurpose.CANONICAL_OBJECT, "geometry-v1", Selector()),
    "survey-control": MigrationPlan(
        "survey-control", 1, "survey-control", PlanPurpose.CANONICAL_OBJECT, "survey-control-v1", Selector(),
    ),
    "addresses": MigrationPlan("addresses", 1, "addresses", PlanPurpose.CANONICAL_OBJECT, "address-v1", Selector()),
    "parcels": MigrationPlan("parcels", 1, "parcels", PlanPurpose.CANONICAL_OBJECT, "parcel-v1", Selector()),
    "titles": MigrationPlan("titles", 1, "titles", PlanPurpose.CANONICAL_OBJECT, "title-v1", Selector()),
    "state-land": MigrationPlan("state-land", 1, "state-land", PlanPurpose.CANONICAL_OBJECT, "state-land-v1", Selector()),
}
for family in (
    "hill", "valley", "river", "forest", "mountain", "lake", "bay", "cape",
    "island", "plain", "plateau", "wetland", "road", "settlement", "administrative",
    "bridge", "landmark", "square",
):
    key = f"names:{family}"
    PLAN_CATALOGUE[key] = MigrationPlan(key, 1, key, PlanPurpose.REFERENCE_CATALOGUE, "geographic-name-reference-v1", Selector())


def get_plan(plan_id: str) -> MigrationPlan:
    try:
        return PLAN_CATALOGUE[plan_id]
    except KeyError as exc:
        raise KeyError(f"unknown NNGLA migration plan: {plan_id}") from exc


__all__ = ["PlanPurpose", "MigrationPlan", "PLAN_CATALOGUE", "get_plan"]
