"""Database execution contract for Bundle 20A; no implicit writes are performed by materialization."""
from __future__ import annotations
from dataclasses import dataclass
from .contracts import RoadAlignment, RoadSegment, RoadNetworkNode, NetworkConnection

@dataclass(frozen=True, slots=True)
class RoadPersistencePlan:
    road: RoadAlignment
    segment: RoadSegment
    start_node: RoadNetworkNode
    end_node: RoadNetworkNode
    connections: tuple[NetworkConnection, NetworkConnection]

    @property
    def target_state(self) -> dict[str,str]:
        return {
            "road.lifecycle_status": "OPERATIONAL_MAPPED",
            "road_reference_candidate.planning_status": "OPERATIONAL",
            "road_reference_candidate.geometry_status": "AUTHORITATIVELY_MAPPED",
            "geometry.publication_status": "NOT_PUBLISHED",
        }
