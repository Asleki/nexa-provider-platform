"""Polygonize-once atomic face construction for Delivery-1 NNGLA recovery.

Topology operations preserve the frozen EPSG:4326 source coordinate semantics.
Residual morphology and area are measured after transforming the *resulting
geometry* to EPSG:6933, matching the controlled live diagnostic method.  This
module never writes to PostgreSQL and never treats a measured tolerance as PASS.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Mapping

from .contracts import FaceClassification, ParentFabricScope
from .edge_graph import SharedEdgeGraph, edge_graph_geometry
from .residual_policy import ResidualClass, classify_residual
from .source import administrative_geometry_payload


class FabricDefectKind(str, Enum):
    PARENT_GAP = "PARENT_GAP"
    SIBLING_OUTSIDE_PARENT = "SIBLING_OUTSIDE_PARENT"
    INDIVIDUAL_SIBLING_OUTSIDE_PARENT = "INDIVIDUAL_SIBLING_OUTSIDE_PARENT"
    POSITIVE_SIBLING_OVERLAP = "POSITIVE_SIBLING_OVERLAP"
    POLYGONIZATION_REMAINDER = "POLYGONIZATION_REMAINDER"


@dataclass(frozen=True, slots=True)
class FabricDefectComponent:
    defect_id: str
    kind: FabricDefectKind
    geometry_sha256: str
    geometry_wkb_hex: str
    area_km2: float
    area_ratio: float
    perimeter_km: float
    effective_width_m: float | None
    adjacent_subject_ids: tuple[str, ...]
    covered_by_subject_ids: tuple[str, ...]
    residual_class: str
    requires_governed_review: bool
    source_subject_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AtomicFace:
    face_id: str
    geometry_sha256: str
    geometry_wkb_hex: str
    area_km2: float
    perimeter_km: float
    classification: FaceClassification
    historical_owner_ids: tuple[str, ...]
    adjacent_subject_ids: tuple[str, ...]
    source_defect_ids: tuple[str, ...]

    @property
    def automatically_owned(self) -> bool:
        return self.classification is FaceClassification.UNIQUE_EXISTING_OWNER and len(self.historical_owner_ids) == 1


@dataclass(frozen=True, slots=True)
class FabricFaceSet:
    scope_fingerprint: str
    edge_graph_sha256: str
    face_set_sha256: str
    parent_area_km2: float
    defects: tuple[FabricDefectComponent, ...]
    faces: tuple[AtomicFace, ...]

    @property
    def governed_face_ids(self) -> tuple[str, ...]:
        return tuple(face.face_id for face in self.faces if not face.automatically_owned)

    @property
    def material_defects(self) -> tuple[FabricDefectComponent, ...]:
        return tuple(item for item in self.defects if item.residual_class == ResidualClass.MATERIAL_TOPOLOGY_FAILURE.value)


def _geometry_engine():
    try:
        from pyproj import Transformer
        from shapely import from_geojson, from_wkb, normalize, to_wkb
        from shapely.geometry import Polygon
        from shapely.ops import polygonize, transform, unary_union
    except ImportError as exc:  # pragma: no cover - environment gate
        raise RuntimeError("shapely and pyproj are required for Delivery-1 face polygonization") from exc
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
    return from_geojson, from_wkb, normalize, to_wkb, Polygon, polygonize, transform, unary_union, transformer


def _load_geometry(subject_id: str, overrides: Mapping[str, object] | None):
    if overrides and subject_id in overrides:
        return overrides[subject_id]
    from_geojson, *_ = _geometry_engine()
    return from_geojson(administrative_geometry_payload(subject_id))


def _polygon_parts(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == "Polygon":
        return [geometry]
    if geometry.geom_type in {"MultiPolygon", "GeometryCollection"}:
        out = []
        for part in geometry.geoms:
            if part.geom_type == "Polygon" and not part.is_empty:
                out.append(part)
            elif part.geom_type == "MultiPolygon":
                out.extend([item for item in part.geoms if not item.is_empty])
        return out
    return []


def _canonical_geometry(geometry):
    _, _, normalize, *_ = _geometry_engine()
    return normalize(geometry)


def _geometry_hash(geometry) -> str:
    _, _, _, to_wkb, *_ = _geometry_engine()
    normalized = _canonical_geometry(geometry)
    return sha256(to_wkb(normalized, hex=False, byte_order=1)).hexdigest()


def _wkb_hex(geometry) -> str:
    _, _, _, to_wkb, *_ = _geometry_engine()
    return to_wkb(_canonical_geometry(geometry), hex=True, byte_order=1)


def _projected(geometry):
    *_, transform, _, transformer = _geometry_engine()
    return transform(transformer.transform, geometry)


def _area_km2(geometry) -> float:
    return float(_projected(geometry).area) / 1_000_000.0


def _perimeter_km(geometry) -> float:
    return float(_projected(geometry).length) / 1000.0


def _adjacency(component, sibling_rows, sibling_geometries) -> tuple[str, ...]:
    rows = []
    for item, geometry in zip(sibling_rows, sibling_geometries):
        intersection = component.boundary.intersection(geometry.boundary)
        if intersection.is_empty:
            continue
        if float(_projected(intersection).length) > 0.0:
            rows.append(item.subject_id)
    return tuple(sorted(set(rows)))


def _covered_by(component, sibling_rows, sibling_geometries) -> tuple[str, ...]:
    point = component.representative_point()
    return tuple(sorted(
        item.subject_id
        for item, geometry in zip(sibling_rows, sibling_geometries)
        if geometry.covers(point)
    ))


def _defect_component(scope, kind, geometry, sibling_rows, sibling_geometries, parent_area_km2, *, source_subject_ids=()):
    area = _area_km2(geometry)
    perimeter = _perimeter_km(geometry)
    ratio = area / parent_area_km2 if parent_area_km2 > 0 else 0.0
    residual = classify_residual(area_km2=area, area_ratio=ratio, difference_dimension=2)
    if kind is FabricDefectKind.SIBLING_OUTSIDE_PARENT:
        requires_review = area > 0.0
    else:
        requires_review = residual is ResidualClass.MATERIAL_TOPOLOGY_FAILURE
    digest = _geometry_hash(geometry)
    return FabricDefectComponent(
        defect_id="fabric-defect:nngla:" + sha256(f"{scope.fingerprint}|{kind.value}|{digest}".encode()).hexdigest(),
        kind=kind,
        geometry_sha256=digest,
        geometry_wkb_hex=_wkb_hex(geometry),
        area_km2=area,
        area_ratio=ratio,
        perimeter_km=perimeter,
        effective_width_m=(2.0 * area * 1_000_000.0 / (perimeter * 1000.0)) if perimeter > 0 else None,
        adjacent_subject_ids=_adjacency(geometry, sibling_rows, sibling_geometries),
        covered_by_subject_ids=_covered_by(geometry, sibling_rows, sibling_geometries),
        residual_class=residual.value,
        requires_governed_review=requires_review,
        source_subject_ids=tuple(sorted(set(source_subject_ids))),
    )


def source_fabric_diagnostics(
    scope: ParentFabricScope,
    *,
    geometry_overrides: Mapping[str, object] | None = None,
) -> tuple[FabricDefectComponent, ...]:
    """Reproduce parent/sibling gap, overshoot and positive overlap evidence."""
    *_, Polygon, _, _, unary_union, _ = _geometry_engine()
    parent = _load_geometry(scope.parent.subject_id, geometry_overrides)
    siblings = [_load_geometry(item.subject_id, geometry_overrides) for item in scope.exhaustive_siblings]
    parent_area = _area_km2(parent)
    sibling_union = unary_union(siblings)
    components = []

    gap = parent.difference(sibling_union)
    for part in _polygon_parts(gap):
        components.append(_defect_component(
            scope, FabricDefectKind.PARENT_GAP, part,
            scope.exhaustive_siblings, siblings, parent_area,
        ))

    # Preserve the union-level overshoot because a non-coincident sibling fabric
    # can create a material union residual even when no individual sibling has
    # a material parent escape (Silvermere's frozen district fabric is the
    # canonical Delivery-1 example).
    outside = sibling_union.difference(parent)
    for part in _polygon_parts(outside):
        components.append(_defect_component(
            scope, FabricDefectKind.SIBLING_OUTSIDE_PARENT, part,
            scope.exhaustive_siblings, siblings, parent_area,
        ))

    # Also preserve each individual child->parent difference.  Union-level
    # geometry can hide an individual parent escape through independent-edge
    # cancellation; the Nyara/Silvermere 0.0334 km² city-parent conflict proves
    # that this evidence must remain separately attributable.
    for item, geometry in zip(scope.exhaustive_siblings, siblings):
        individual_outside = geometry.difference(parent)
        if not individual_outside.is_empty:
            # Keep the complete child->parent residual together.  R3/PostGIS
            # classifies this predicate on the whole difference geometry, and
            # splitting a multi-strip residual before policy classification can
            # incorrectly downgrade a material aggregate into several micros.
            components.append(_defect_component(
                scope, FabricDefectKind.INDIVIDUAL_SIBLING_OUTSIDE_PARENT, individual_outside,
                scope.exhaustive_siblings, siblings, parent_area,
                source_subject_ids=(item.subject_id,),
            ))

    overlap_parts = []
    for index, left in enumerate(siblings):
        for right in siblings[index + 1:]:
            intersection = left.intersection(right).intersection(parent)
            overlap_parts.extend(part for part in _polygon_parts(intersection) if part.area > 0.0)
    if overlap_parts:
        overlap_union = unary_union(overlap_parts)
        for part in _polygon_parts(overlap_union):
            components.append(_defect_component(
                scope, FabricDefectKind.POSITIVE_SIBLING_OVERLAP, part,
                scope.exhaustive_siblings, siblings, parent_area,
            ))

    return tuple(sorted(components, key=lambda item: (item.kind.value, item.geometry_sha256)))


def _make_face(scope, geometry, classification, historical_owner_ids, adjacent_subject_ids, source_defect_ids):
    digest = _geometry_hash(geometry)
    return AtomicFace(
        face_id="fabric-face:nngla:" + sha256(f"{scope.fingerprint}|{digest}".encode()).hexdigest(),
        geometry_sha256=digest,
        geometry_wkb_hex=_wkb_hex(geometry),
        area_km2=_area_km2(geometry),
        perimeter_km=_perimeter_km(geometry),
        classification=classification,
        historical_owner_ids=tuple(sorted(set(historical_owner_ids))),
        adjacent_subject_ids=tuple(sorted(set(adjacent_subject_ids))),
        source_defect_ids=tuple(sorted(set(source_defect_ids))),
    )


def build_atomic_face_set(
    scope: ParentFabricScope,
    edge_graph: SharedEdgeGraph,
    *,
    geometry_overrides: Mapping[str, object] | None = None,
) -> FabricFaceSet:
    """Build stable ownership faces plus explicit gap/overlap defect faces.

    Material source defects are not assigned here.  They survive as governed
    atomic faces so later face assignment cannot silently hide the evidence.
    """
    _, _, _, _, Polygon, polygonize, _, unary_union, _ = _geometry_engine()
    parent = _load_geometry(scope.parent.subject_id, geometry_overrides)
    siblings = [_load_geometry(item.subject_id, geometry_overrides) for item in scope.exhaustive_siblings]
    defects = source_fabric_diagnostics(scope, geometry_overrides=geometry_overrides)
    parent_area = _area_km2(parent)

    in_parent_defects = [
        item for item in defects
        if item.kind in {FabricDefectKind.PARENT_GAP, FabricDefectKind.POSITIVE_SIBLING_OVERLAP}
    ]
    from shapely import from_wkb
    defect_geometries = {
        item.defect_id: from_wkb(bytes.fromhex(item.geometry_wkb_hex))
        for item in in_parent_defects
    }
    defect_domain = unary_union(list(defect_geometries.values())) if defect_geometries else Polygon()

    stable_domains = []
    for item, geometry in zip(scope.exhaustive_siblings, siblings):
        stable = geometry.intersection(parent)
        if not defect_domain.is_empty:
            stable = stable.difference(defect_domain)
        stable_domains.append((item.subject_id, stable))

    graph = edge_graph_geometry(edge_graph)
    if not defect_domain.is_empty:
        from shapely import node
        graph = node(unary_union([graph, defect_domain.boundary]))
    raw_faces = list(polygonize(graph))
    faces = []

    for raw in raw_faces:
        within_parent = raw.intersection(parent)
        if within_parent.is_empty:
            continue
        for owner_id, stable_domain in stable_domains:
            for part in _polygon_parts(within_parent.intersection(stable_domain)):
                if part.area <= 0.0:
                    continue
                faces.append(_make_face(
                    scope, part, FaceClassification.UNIQUE_EXISTING_OWNER,
                    (owner_id,), _adjacency(part, scope.exhaustive_siblings, siblings), (),
                ))
        for defect in in_parent_defects:
            defect_geometry = defect_geometries[defect.defect_id]
            for part in _polygon_parts(within_parent.intersection(defect_geometry)):
                if part.area <= 0.0 and _area_km2(part) <= 0.0:
                    continue
                if defect.kind is FabricDefectKind.POSITIVE_SIBLING_OVERLAP:
                    classification = FaceClassification.MULTIPLE_EXISTING_OWNERS
                    owners = defect.covered_by_subject_ids
                elif defect.residual_class == ResidualClass.MATERIAL_TOPOLOGY_FAILURE.value:
                    classification = FaceClassification.MATERIAL_UNASSIGNED
                    owners = ()
                else:
                    classification = FaceClassification.MICRO_UNASSIGNED
                    owners = ()
                faces.append(_make_face(
                    scope, part, classification, owners,
                    defect.adjacent_subject_ids, (defect.defect_id,),
                ))

    # Floating overlay engines can leave an unrepresented in-parent polygon even
    # after polygonize-once.  Preserve it as evidence instead of auto-snapping it.
    face_geometries = [from_wkb(bytes.fromhex(item.geometry_wkb_hex)) for item in faces]
    represented = unary_union(face_geometries) if face_geometries else Polygon()
    remainder = parent.difference(represented)
    for part in _polygon_parts(remainder):
        if part.is_empty:
            continue
        digest = _geometry_hash(part)
        remainder_defect = _defect_component(
            scope, FabricDefectKind.POLYGONIZATION_REMAINDER, part,
            scope.exhaustive_siblings, siblings, parent_area,
        )
        defects = tuple(defects) + (remainder_defect,)
        faces.append(_make_face(
            scope, part, FaceClassification.AMBIGUOUS_PROVENANCE,
            (), remainder_defect.adjacent_subject_ids, (remainder_defect.defect_id,),
        ))

    # Deduplicate only byte-identical face geometry/classification combinations.
    unique = {}
    for face in faces:
        key = (face.geometry_sha256, face.classification.value, face.historical_owner_ids, face.source_defect_ids)
        unique.setdefault(key, face)
    ordered_faces = tuple(sorted(unique.values(), key=lambda item: (item.geometry_sha256, item.classification.value, item.face_id)))
    ordered_defects = tuple(sorted({item.defect_id: item for item in defects}.values(), key=lambda item: (item.kind.value, item.geometry_sha256)))
    face_material = {
        "scope": scope.fingerprint,
        "graph": edge_graph.graph_sha256,
        "faces": [
            (item.geometry_sha256, item.classification.value, item.historical_owner_ids, item.source_defect_ids)
            for item in ordered_faces
        ],
        "defects": [(item.kind.value, item.geometry_sha256, item.residual_class) for item in ordered_defects],
    }
    face_set_sha = sha256(json.dumps(face_material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return FabricFaceSet(
        scope_fingerprint=scope.fingerprint,
        edge_graph_sha256=edge_graph.graph_sha256,
        face_set_sha256=face_set_sha,
        parent_area_km2=parent_area,
        defects=ordered_defects,
        faces=ordered_faces,
    )


__all__ = [
    "FabricDefectKind",
    "FabricDefectComponent",
    "AtomicFace",
    "FabricFaceSet",
    "source_fabric_diagnostics",
    "build_atomic_face_set",
]
