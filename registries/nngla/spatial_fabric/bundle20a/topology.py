"""Road-node, segment and connectivity derivation for Bundle 20A."""
from __future__ import annotations
from collections import Counter
from ._shared import stable_id
from .contracts import RoadAlignment, RoadNetworkNode, RoadSegment, NetworkConnection
from .authoring import author_road_alignments
from .source import place_rows


def build_network(alignments: tuple[RoadAlignment,...] | None = None):
    roads = alignments or author_road_alignments()
    places = {r["place_id"]: r for r in place_rows()}
    degree = Counter()
    for r in roads:
        degree[r.start_place_id] += 1; degree[r.end_place_id] += 1
    node_by_place: dict[str,RoadNetworkNode] = {}
    for place_id in sorted(degree):
        p = places[place_id]
        node_by_place[place_id] = RoadNetworkNode(
            node_id=stable_id("roadnode:nngla:", place_id), longitude=float(p["longitude"]), latitude=float(p["latitude"]),
            place_id=place_id, region_code=p["region_code"], node_role="JUNCTION" if degree[place_id] > 1 else "ENDPOINT",
        )
    segments: list[RoadSegment] = []
    connections: list[NetworkConnection] = []
    for r in roads:
        sid = stable_id("roadseg:nngla:", r.road_id, 1, r.start_place_id, r.end_place_id)
        s = RoadSegment(sid, r.road_id, r.road_candidate_id, 1, node_by_place[r.start_place_id].node_id,
                        node_by_place[r.end_place_id].node_id, r.length_m, True, r.geometry_reservation_key)
        segments.append(s)
        connections.extend([
            NetworkConnection(stable_id("roadconn:nngla:", sid, "START"), s.start_node_id, sid, r.road_id, "START"),
            NetworkConnection(stable_id("roadconn:nngla:", sid, "END"), s.end_node_id, sid, r.road_id, "END"),
        ])
    return tuple(node_by_place[p] for p in sorted(node_by_place)), tuple(segments), tuple(connections)
