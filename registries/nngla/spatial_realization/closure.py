"""Automatic dependency closure for selected major-city roots."""
from __future__ import annotations

from functools import lru_cache

from .contracts import CityClosure, Dependency, DependencyRole
from .selection import normalize_city_root_ids
from .source import (
    administrative_reference_seeds,
    administrative_source_rows,
    city_root_by_id,
    geometry_for_admin,
    place_footprint_candidate,
    place_point_candidate,
    reference_point_support,
)


@lru_cache(maxsize=8)
def build_city_closure(root_place_id: str) -> CityClosure:
    root = city_root_by_id().get(root_place_id)
    if root is None:
        raise ValueError(f"unknown major-city root {root_place_id}")
    admins = administrative_source_rows()
    by_id = {item.administrative_area_id: item for item in admins}
    if root.administrative_area_id not in by_id or root.validation_parent_id not in by_id:
        raise ValueError("city administrative root or validation parent is absent from locked Bundle 19B")

    direct_children = tuple(
        item for item in admins if item.parent_administrative_area_id == root.administrative_area_id
    )
    exhaustive = tuple(sorted(
        (item for item in direct_children if item.administrative_type_code == "CITY_DISTRICT"),
        key=lambda item: int(item.administrative_area_id.rsplit("-", 1)[1]),
    ))
    overlays = tuple(sorted(
        (item for item in direct_children if item.administrative_type_code == "INDUSTRIAL_ZONE"),
        key=lambda item: int(item.administrative_area_id.rsplit("-", 1)[1]),
    ))
    unsupported = tuple(
        item.administrative_area_id
        for item in direct_children
        if item.administrative_type_code not in {"CITY_DISTRICT", "INDUSTRIAL_ZONE"}
    )
    if unsupported:
        raise ValueError("unsupported direct city administrative child roles: " + ",".join(unsupported))
    if not exhaustive:
        raise ValueError(f"major-city root has no exhaustive CITY_DISTRICT closure: {root_place_id}")

    # Region-level peers are validation context, never automatic mutations for a
    # city-root run.  This makes parent-fabric defects visible without allowing a
    # selected city to rewrite sibling municipalities.
    regional_peers = tuple(sorted(
        (
            item for item in admins
            if item.parent_administrative_area_id == root.validation_parent_id
            and item.administrative_type_code in {"CITY", "MUNICIPALITY"}
        ),
        key=lambda item: int(item.administrative_area_id.rsplit("-", 1)[1]),
    ))
    if not any(item.administrative_area_id == root.administrative_area_id for item in regional_peers):
        raise ValueError("selected city is absent from its regional partition context")

    place_ref = place_point_candidate(root.place_id)
    footprint = place_footprint_candidate(root.place_id)
    admin_root = geometry_for_admin(root.administrative_area_id, root.place_id)
    child_candidates = tuple(geometry_for_admin(item.administrative_area_id, root.place_id) for item in exhaustive)
    child_seeds = administrative_reference_seeds(item.administrative_area_id for item in exhaustive)
    overlay_candidates = tuple(geometry_for_admin(item.administrative_area_id, root.place_id) for item in overlays)
    validation_parent = geometry_for_admin(root.validation_parent_id, root.place_id)
    peer_candidates = tuple(geometry_for_admin(item.administrative_area_id, root.place_id) for item in regional_peers)
    support = reference_point_support(root.place_id)

    dependencies = [
        Dependency(root.place_id, DependencyRole.EXECUTION_ROOT, root.place_id, "PLACE", True),
        Dependency(root.place_id, DependencyRole.PLACE_SUBJECT, root.place_id, "PLACE", True),
        Dependency(root.place_id, DependencyRole.PLACE_REFERENCE_SOURCE, place_ref.source_candidate_id, "EVIDENCE", False),
        Dependency(root.place_id, DependencyRole.SUPPORTING_SPATIAL_REFERENCE, support, "SPATIAL_REFERENCE_POINT", False),
        Dependency(root.place_id, DependencyRole.EXECUTION_ADMIN_ROOT, root.administrative_area_id, "ADMINISTRATIVE_AREA", True),
        Dependency(root.place_id, DependencyRole.VALIDATION_PARENT, root.validation_parent_id, "ADMINISTRATIVE_AREA", False),
    ]
    dependencies.extend(
        Dependency(root.place_id, DependencyRole.EXHAUSTIVE_CHILD, item.subject_id, "ADMINISTRATIVE_AREA", True)
        for item in child_candidates
    )
    dependencies.extend(
        Dependency(root.place_id, DependencyRole.NON_EXHAUSTIVE_OVERLAY, item.subject_id, "ADMINISTRATIVE_AREA", False)
        for item in overlay_candidates
    )
    dependencies.extend(
        Dependency(root.place_id, DependencyRole.VALIDATION_PEER, item.subject_id, "ADMINISTRATIVE_AREA", False)
        for item in peer_candidates if item.subject_id != root.administrative_area_id
    )
    if footprint is not None:
        dependencies.append(
            Dependency(root.place_id, DependencyRole.UNCHANGED_REFERENCE, footprint.source_candidate_id, "SETTLEMENT_FOOTPRINT_SOURCE", False)
        )

    return CityClosure(
        root=root,
        place_reference=place_ref,
        settlement_footprint=footprint,
        admin_root=admin_root,
        exhaustive_children=child_candidates,
        overlays=overlay_candidates,
        validation_parent=validation_parent,
        regional_partition_peers=peer_candidates,
        supporting_spatial_point_id=support,
        exhaustive_child_seeds=child_seeds,
        dependencies=tuple(dependencies),
    )


def build_selection_closure(root_ids) -> tuple[CityClosure, ...]:
    normalized = normalize_city_root_ids(root_ids)
    return tuple(build_city_closure(root_id) for root_id in normalized)


__all__ = ["build_city_closure", "build_selection_closure"]
