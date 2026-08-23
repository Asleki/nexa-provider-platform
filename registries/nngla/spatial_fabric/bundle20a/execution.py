"""Build deterministic live-execution plans after governed geometry-ID reservation."""
from __future__ import annotations
from .authoring import author_road_alignments
from .topology import build_network
from .persistence import RoadPersistencePlan

def execution_plans():
    roads=author_road_alignments(); nodes,segs,conns=build_network(roads); bynode={n.node_id:n for n in nodes}; byroad={r.road_id:r for r in roads}; conn={}
    for c in conns: conn.setdefault(c.road_id,[]).append(c)
    return tuple(RoadPersistencePlan(byroad[s.road_id],s,bynode[s.start_node_id],bynode[s.end_node_id],tuple(sorted(conn[s.road_id],key=lambda x:x.endpoint_role))) for s in segs)
