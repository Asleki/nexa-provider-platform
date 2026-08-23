"""Stable Bundle 20A contracts for governed road geometry and topology."""
from __future__ import annotations
from dataclasses import dataclass
import re
from ._shared import CRS_CODE, EFFECT_SCOPE, GEOMETRY_ROLE

_RD = re.compile(r"^NG-RD-\d{6}$")
_CAND = re.compile(r"^NG-RD-CAND-\d{6}$")
_PLC = re.compile(r"^NG-PLC-\d{6}$")

@dataclass(frozen=True, slots=True)
class RoadAlignment:
    road_id: str
    road_candidate_id: str
    road_name_id: str
    canonical_name: str
    road_class_code: str
    region_code: str
    start_place_id: str
    end_place_id: str
    coordinates: tuple[tuple[float, float], ...]
    length_m: float
    geometry_reservation_key: str
    geometry_role_code: str = GEOMETRY_ROLE
    crs_code: str = CRS_CODE
    qualification_status: str = "QUALIFIED_SIMULATION_AUTHORED"
    provenance_class: str = "NNGLA_SIMULATION_AUTHORED_ALIGNMENT"
    runtime_effect_scope: str = EFFECT_SCOPE

    def __post_init__(self) -> None:
        if not _RD.fullmatch(self.road_id) or not _CAND.fullmatch(self.road_candidate_id):
            raise ValueError("invalid road identity")
        if not _PLC.fullmatch(self.start_place_id) or not _PLC.fullmatch(self.end_place_id) or self.start_place_id == self.end_place_id:
            raise ValueError("road endpoints require two distinct canonical places")
        if len(self.coordinates) < 2 or self.length_m <= 0:
            raise ValueError("road alignment requires non-zero LINESTRING geometry")
        if self.crs_code != CRS_CODE or self.geometry_role_code != GEOMETRY_ROLE:
            raise ValueError("road alignment must use governed CRS and ROAD_ALIGNMENT role")
        if not self.geometry_reservation_key.startswith("p006.7.11.12:road-alignment:"):
            raise ValueError("invalid road geometry reservation key")
        if self.runtime_effect_scope != EFFECT_SCOPE:
            raise ValueError("road geography remains SHARED_REFERENCE")

@dataclass(frozen=True, slots=True)
class RoadNetworkNode:
    node_id: str
    longitude: float
    latitude: float
    place_id: str
    region_code: str
    node_role: str

    def __post_init__(self) -> None:
        if not self.node_id.startswith("roadnode:nngla:") or not _PLC.fullmatch(self.place_id):
            raise ValueError("invalid road node identity")
        if self.node_role not in {"ENDPOINT", "JUNCTION"}:
            raise ValueError("invalid road node role")

@dataclass(frozen=True, slots=True)
class RoadSegment:
    road_segment_id: str
    road_id: str
    road_candidate_id: str
    segment_sequence: int
    start_node_id: str
    end_node_id: str
    length_m: float
    addressing_scope_eligible: bool
    geometry_reservation_key: str

    def __post_init__(self) -> None:
        if not self.road_segment_id.startswith("roadseg:nngla:") or not _RD.fullmatch(self.road_id):
            raise ValueError("invalid road segment identity")
        if self.segment_sequence < 1 or self.start_node_id == self.end_node_id or self.length_m <= 0:
            raise ValueError("invalid road segment topology")

@dataclass(frozen=True, slots=True)
class NetworkConnection:
    connection_id: str
    node_id: str
    road_segment_id: str
    road_id: str
    endpoint_role: str

    def __post_init__(self) -> None:
        if not self.connection_id.startswith("roadconn:nngla:") or self.endpoint_role not in {"START", "END"}:
            raise ValueError("invalid network connection")

@dataclass(frozen=True, slots=True)
class RoadSpatialRelationship:
    relationship_id: str
    road_id: str
    relationship_type: str
    object_id: str
    evidence_basis: str
    longitude: float | None = None
    latitude: float | None = None

    def __post_init__(self) -> None:
        if not self.relationship_id.startswith("roadrel:nngla:") or not _RD.fullmatch(self.road_id):
            raise ValueError("invalid road relationship identity")
        if self.relationship_type not in {"STARTS_AT_PLACE", "ENDS_AT_PLACE", "WITHIN_ADMIN_REGION", "CROSSES_RIVER", "INTERSECTS_LAKE"}:
            raise ValueError("unsupported road relationship")
