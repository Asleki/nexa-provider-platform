"""P006.7.11.4 deterministic, zero-write NNGLA migration previews."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from collections import Counter
from collections.abc import Mapping

from .plans import MigrationPlan, get_plan
from .qualification import QualificationEngine, QualificationOutcome, RecordQualification
from .selectors import Selector, select_records
from .source_catalogue import SourceKind, load_source


@dataclass(frozen=True, slots=True)
class TargetStateSnapshot:
    database_name: str
    environment_name: str
    schema_capabilities: frozenset[str] = frozenset()
    occupied_canonical_ids: frozenset[str] = frozenset()
    crosswalks: Mapping[str, str] | None = None

    @classmethod
    def unavailable(cls, database_name: str = "UNRESOLVED", environment_name: str = "UNRESOLVED") -> "TargetStateSnapshot":
        return cls(database_name, environment_name)


@dataclass(frozen=True, slots=True)
class MigrationPreview:
    plan_id: str
    plan_version: int
    source_key: str
    source_sha256: str
    source_count: int
    selected_count: int
    qualification_counts: Mapping[str, int]
    proposed_canonical_ids: tuple[str, ...]
    selected_source_ids: tuple[str, ...]
    findings: tuple[RecordQualification, ...]
    database_name: str
    environment_name: str
    schema_ready: bool
    execution_ready: bool
    fingerprint: str
    database_writes: int = 0


_REQUIRED_SCHEMA_CAPABILITY = {
    "sovereign-boundary": "world_geometry_authority",
    "places": "nngla_geographic_identity_places",
    "administrative-areas": "nngla_geographic_identity_places",
    "roads": "nngla_geometry_roads_addresses",
    "geographic-features": "nngla_geographic_identity_places",
    "geometry": "nngla_geometry_roads_addresses",
    "survey-control": "nngla_geometry_roads_addresses",
    "addresses": "nngla_geometry_roads_addresses",
    "parcels": "nngla_cadastre_titles_state_land",
    "titles": "nngla_cadastre_titles_state_land",
    "state-land": "nngla_cadastre_titles_state_land",
}


class PreviewService:
    def __init__(self) -> None:
        self._qualification = QualificationEngine()

    def preview(
        self,
        plan_id: str,
        *,
        selector_override: Selector | None = None,
        target: TargetStateSnapshot | None = None,
        repository_revision: str = "UNRESOLVED",
    ) -> MigrationPreview:
        base = get_plan(plan_id)
        plan = base.with_selector(selector_override) if selector_override is not None else base
        snapshot = load_source(plan.source_key)
        target = target or TargetStateSnapshot.unavailable()
        selected = select_records(snapshot.records, plan.selector)
        results = tuple(self._qualification.qualify(plan, snapshot, record) for record in selected)

        canonical_ids = tuple(sorted(r.proposed_canonical_id for r in results if r.proposed_canonical_id))
        collisions = {cid for cid, count in Counter(canonical_ids).items() if count > 1}
        occupied = set(target.occupied_canonical_ids)
        target_collisions = set(canonical_ids) & occupied
        counts = Counter(r.outcome.value for r in results)
        if snapshot.governed_empty:
            counts[QualificationOutcome.EMPTY_GOVERNED_SOURCE.value] = 1

        capability = self._capability(plan.source_key)
        schema_ready = capability is None or capability in target.schema_capabilities
        all_records_qualified = all(r.outcome in {QualificationOutcome.QUALIFIED, QualificationOutcome.QUALIFIED_WITH_REUSE} for r in results)
        execution_ready = schema_ready and not collisions and not target_collisions and all_records_qualified
        if snapshot.governed_empty:
            execution_ready = schema_ready

        fingerprint_payload = {
            "plan_id": plan.plan_id,
            "plan_version": plan.version,
            "source_key": plan.source_key,
            "source_sha256": snapshot.source_sha256,
            "selected_source_ids": [r.source_id for r in selected],
            "selector": {
                "kind": plan.selector.kind.value,
                "field": plan.selector.field,
                "values": list(plan.selector.values),
                "exact_ids": list(plan.selector.exact_ids),
                "after_id": plan.selector.after_id,
                "limit": plan.selector.limit,
            },
            "runtime_mode": plan.runtime_mode,
            "effect_scope": plan.effect_scope,
            "qualification_profile": plan.qualification_profile,
            "proposed_canonical_ids": list(canonical_ids),
            "database_name": target.database_name,
            "environment_name": target.environment_name,
            "repository_revision": repository_revision,
        }
        fingerprint = sha256(json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return MigrationPreview(
            plan.plan_id,
            plan.version,
            plan.source_key,
            snapshot.source_sha256,
            len(snapshot.records),
            len(selected),
            dict(sorted(counts.items())),
            canonical_ids,
            tuple(r.source_id for r in selected),
            results,
            target.database_name,
            target.environment_name,
            schema_ready,
            execution_ready,
            fingerprint,
            0,
        )

    @staticmethod
    def _capability(source_key: str) -> str | None:
        if source_key.startswith("names:"):
            return "nngla_geographic_identity_places"
        return _REQUIRED_SCHEMA_CAPABILITY.get(source_key)


__all__ = ["TargetStateSnapshot", "MigrationPreview", "PreviewService"]
