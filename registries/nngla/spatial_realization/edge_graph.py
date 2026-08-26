"""Common noded edge graph for Delivery-1 parent-scoped shared-face fabrics."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Mapping

from .contracts import FabricInputRole, ParentFabricScope
from .source import administrative_geometry_payload

LINEAGE_DISTANCE_EPSILON_DEGREES = 1e-12


def _require_geometry_engine():
    try:
        from shapely import from_geojson, node
        from shapely.geometry import LineString
        from shapely.ops import unary_union
    except ImportError as exc:  # pragma: no cover - environment gate
        raise RuntimeError("shapely is required for Delivery-1 shared edge graphs") from exc
    return from_geojson, node, LineString, unary_union


def _canonical_segment(line_string_cls, a, b):
    left = (float(a[0]), float(a[1]))
    right = (float(b[0]), float(b[1]))
    if right < left:
        left, right = right, left
    return line_string_cls((left, right))


def _geometry_sha256(geometry) -> str:
    from shapely import to_wkb
    return sha256(to_wkb(geometry, hex=False, byte_order=1)).hexdigest()


@dataclass(frozen=True, slots=True)
class EdgeSourceLineage:
    subject_id: str
    source_candidate_id: str
    input_role: str


@dataclass(frozen=True, slots=True)
class SharedEdge:
    edge_id: str
    geometry_sha256: str
    geometry_wkb_hex: str
    lineage: tuple[EdgeSourceLineage, ...]


@dataclass(frozen=True, slots=True)
class SharedEdgeGraph:
    scope_fingerprint: str
    graph_sha256: str
    edges: tuple[SharedEdge, ...]
    source_subject_ids: tuple[str, ...]

    @property
    def edge_count(self) -> int:
        return len(self.edges)


def _load_geometry(subject_id: str, overrides: Mapping[str, object] | None):
    if overrides and subject_id in overrides:
        return overrides[subject_id]
    from_geojson, _, _, _ = _require_geometry_engine()
    return from_geojson(administrative_geometry_payload(subject_id))


def build_shared_edge_graph(
    scope: ParentFabricScope,
    *,
    geometry_overrides: Mapping[str, object] | None = None,
) -> SharedEdgeGraph:
    """Node the parent plus every exhaustive sibling boundary exactly once.

    Non-exhaustive overlays are intentionally excluded from territorial edge
    ownership.  They remain in the scope manifest for later evidence checks.
    """
    _, node, line_string_cls, unary_union = _require_geometry_engine()
    inputs = (scope.parent,) + scope.exhaustive_siblings
    source_lines = []
    source_meta = []
    for item in inputs:
        geometry = _load_geometry(item.subject_id, geometry_overrides)
        if geometry.is_empty or geometry.geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"fabric input is not a non-empty polygon: {item.subject_id}")
        source_lines.append(geometry.boundary)
        source_meta.append((item, geometry.boundary))

    noded = node(unary_union(source_lines))
    raw_segments = {}
    parts = list(noded.geoms) if hasattr(noded, "geoms") else [noded]
    for part in parts:
        if part.geom_type != "LineString":
            continue
        coordinates = list(part.coords)
        for start, end in zip(coordinates, coordinates[1:]):
            if start == end:
                continue
            segment = _canonical_segment(line_string_cls, start, end)
            digest = _geometry_sha256(segment)
            raw_segments.setdefault(digest, segment)

    edges = []
    for digest, segment in sorted(raw_segments.items()):
        lineage = []
        for item, source_boundary in source_meta:
            intersection = segment.intersection(source_boundary)
            if (not intersection.is_empty and float(intersection.length) > 0.0) or float(source_boundary.distance(segment)) <= LINEAGE_DISTANCE_EPSILON_DEGREES:
                lineage.append(EdgeSourceLineage(
                    subject_id=item.subject_id,
                    source_candidate_id=item.source_candidate_id,
                    input_role=item.input_role.value,
                ))
        if not lineage:
            raise RuntimeError("noded edge has no source lineage")
        lineage = tuple(sorted(lineage, key=lambda row: (row.subject_id, row.source_candidate_id, row.input_role)))
        from shapely import to_wkb
        edges.append(SharedEdge(
            edge_id="fabric-edge:nngla:" + digest,
            geometry_sha256=digest,
            geometry_wkb_hex=to_wkb(segment, hex=True, byte_order=1),
            lineage=lineage,
        ))

    if not edges:
        raise RuntimeError("shared edge graph is empty")
    graph_material = {
        "scope": scope.fingerprint,
        "edges": [(edge.geometry_sha256, [(x.subject_id, x.source_candidate_id, x.input_role) for x in edge.lineage]) for edge in edges],
    }
    graph_sha = sha256(json.dumps(graph_material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    observed_sources = {lineage.subject_id for edge in edges for lineage in edge.lineage}
    expected_sources = {item.subject_id for item in inputs}
    if observed_sources != expected_sources:
        missing = sorted(expected_sources - observed_sources)
        raise RuntimeError("shared edge graph lost source lineage: " + ",".join(missing))
    return SharedEdgeGraph(
        scope_fingerprint=scope.fingerprint,
        graph_sha256=graph_sha,
        edges=tuple(edges),
        source_subject_ids=tuple(item.subject_id for item in inputs),
    )


def edge_graph_geometry(graph: SharedEdgeGraph):
    """Reconstitute the immutable noded graph from its atomic edge records."""
    from shapely import from_wkb
    from shapely.ops import unary_union
    return unary_union([from_wkb(bytes.fromhex(edge.geometry_wkb_hex)) for edge in graph.edges])


__all__ = [
    "LINEAGE_DISTANCE_EPSILON_DEGREES",
    "EdgeSourceLineage",
    "SharedEdge",
    "SharedEdgeGraph",
    "build_shared_edge_graph",
    "edge_graph_geometry",
]
