"""Parent-scoped hierarchy resolution for Delivery-1 shared-face reconstruction.

This module is read-only.  It resolves the *complete exhaustive sibling set* at
the tier that must be reconstructed together; overlays are carried as evidence
but never become territorial owners.
"""
from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json

from .contracts import (
    FabricInput,
    FabricInputRole,
    FabricLevel,
    ParentFabricScope,
)
from .runtime_signature import detect_runtime_signature
from .source import (
    administrative_children,
    administrative_input,
    administrative_row,
    city_root_by_id,
)

EXHAUSTIVE_CHILD_TYPES = {
    "REGION": frozenset({"CITY", "MUNICIPALITY"}),
    "CITY": frozenset({"CITY_DISTRICT"}),
    "MUNICIPALITY": frozenset({"TOWNSHIP"}),
}
OVERLAY_TYPES = frozenset({"INDUSTRIAL_ZONE"})

LEVEL_BY_PARENT_TYPE = {
    "REGION": FabricLevel.REGION_LOCAL_AREAS,
    "CITY": FabricLevel.CITY_DISTRICTS,
    "MUNICIPALITY": FabricLevel.MUNICIPALITY_TOWNSHIPS,
}


def _digest_payload(payload: object) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def build_parent_fabric_scope(
    requested_root_place_id: str,
    parent_administrative_area_id: str,
    *,
    runtime_signature=None,
    parent_input_override: FabricInput | None = None,
) -> ParentFabricScope:
    root = city_root_by_id().get(requested_root_place_id)
    if root is None:
        raise ValueError(f"unknown major-city root {requested_root_place_id}")
    parent_row = administrative_row(parent_administrative_area_id)
    child_types = EXHAUSTIVE_CHILD_TYPES.get(parent_row.administrative_type_code)
    if not child_types:
        raise ValueError(f"administrative type {parent_row.administrative_type_code} is not an exhaustive Delivery-1 parent")

    children = administrative_children(parent_administrative_area_id)
    exhaustive_rows = tuple(row for row in children if row.administrative_type_code in child_types)
    overlay_rows = tuple(row for row in children if row.administrative_type_code in OVERLAY_TYPES)
    unexpected = tuple(row for row in children if row.administrative_type_code not in child_types | OVERLAY_TYPES)
    if unexpected:
        raise ValueError(
            "unclassified direct administrative children: "
            + ",".join(row.administrative_area_id for row in unexpected)
        )
    if not exhaustive_rows:
        raise ValueError("parent fabric scope has no exhaustive siblings")

    parent = parent_input_override or administrative_input(parent_administrative_area_id, FabricInputRole.PARENT)
    if parent.subject_id != parent_administrative_area_id or parent.input_role is not FabricInputRole.PARENT:
        raise ValueError("parent input override does not match requested fabric parent")
    exhaustive = tuple(
        administrative_input(row.administrative_area_id, FabricInputRole.EXHAUSTIVE_SIBLING)
        for row in exhaustive_rows
    )
    overlays = tuple(
        administrative_input(row.administrative_area_id, FabricInputRole.NON_EXHAUSTIVE_OVERLAY)
        for row in overlay_rows
    )
    runtime = runtime_signature or detect_runtime_signature()
    input_payload = {
        "parent": (parent.subject_id, parent.source_candidate_id, parent.geometry_checksum_sha256),
        "siblings": [
            (item.subject_id, item.source_candidate_id, item.geometry_checksum_sha256)
            for item in exhaustive
        ],
        "overlays": [
            (item.subject_id, item.source_candidate_id, item.geometry_checksum_sha256)
            for item in overlays
        ],
        "runtime": runtime.digest,
    }
    input_digest = _digest_payload(input_payload)
    scope_material = {
        "requested_root_place_id": requested_root_place_id,
        "parent": parent.subject_id,
        "level": LEVEL_BY_PARENT_TYPE[parent_row.administrative_type_code].value,
        "input": input_digest,
    }
    scope_id = "fabric-scope:nngla:" + _digest_payload(scope_material)
    return ParentFabricScope(
        scope_id=scope_id,
        requested_root_place_id=requested_root_place_id,
        parent=parent,
        level=LEVEL_BY_PARENT_TYPE[parent_row.administrative_type_code],
        exhaustive_siblings=exhaustive,
        overlays=overlays,
        runtime_signature=runtime,
        input_digest=input_digest,
    )


def resolve_initial_fabric_scope(
    requested_root_place_id: str,
    *,
    material_rule_codes=(),
    runtime_signature=None,
) -> ParentFabricScope:
    """Resolve the highest scope implicated by the supplied material findings.

    A material city/parent containment failure moves the first authoring scope
    upward to the region so all city/municipality peers are considered together.
    Otherwise the selected city's own exhaustive children are the first scope.
    """
    root = city_root_by_id().get(requested_root_place_id)
    if root is None:
        raise ValueError(f"unknown major-city root {requested_root_place_id}")
    codes = frozenset(str(code).strip() for code in material_rule_codes if str(code).strip())
    parent_id = root.validation_parent_id if "CITY_PARENT_CONTAINMENT_FAILED" in codes else root.administrative_area_id
    return build_parent_fabric_scope(
        requested_root_place_id,
        parent_id,
        runtime_signature=runtime_signature,
    )


def build_recursive_child_scope(
    parent_scope: ParentFabricScope,
    child_parent_administrative_area_id: str,
    *,
    qualified_parent_geometry_sha256: str,
    qualified_parent_candidate_id: str,
) -> ParentFabricScope:
    """Bind a descendant run to the exact qualified parent candidate hash."""
    source_parent = administrative_input(child_parent_administrative_area_id, FabricInputRole.PARENT)
    if child_parent_administrative_area_id not in {item.subject_id for item in parent_scope.exhaustive_siblings}:
        raise ValueError("recursive child parent is not an exhaustive member of the qualified parent scope")
    override = replace(
        source_parent,
        source_candidate_id=str(qualified_parent_candidate_id).strip(),
        geometry_checksum_sha256=str(qualified_parent_geometry_sha256).strip(),
        source_path_reference=f"derived-from:{parent_scope.scope_id}",
    )
    return build_parent_fabric_scope(
        parent_scope.requested_root_place_id,
        child_parent_administrative_area_id,
        runtime_signature=parent_scope.runtime_signature,
        parent_input_override=override,
    )


__all__ = [
    "EXHAUSTIVE_CHILD_TYPES",
    "OVERLAY_TYPES",
    "LEVEL_BY_PARENT_TYPE",
    "build_parent_fabric_scope",
    "resolve_initial_fabric_scope",
    "build_recursive_child_scope",
]
