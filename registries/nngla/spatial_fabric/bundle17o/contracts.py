"""Stable spatial query and read-result contracts."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from collections.abc import Mapping
from shared.runtime.operation_runtime import OperationRuntimeMode

class QueryOperator(str, Enum):
    CONTAINS="CONTAINS"; WITHIN="WITHIN"; INTERSECTS="INTERSECTS"; CROSSES="CROSSES"
    TOUCHES="TOUCHES"; ADJACENT="ADJACENT"; NEAREST="NEAREST"; DISTANCE="DISTANCE"
    FRONTS="FRONTS"; CONNECTED_TO="CONNECTED_TO"

class BoundaryPolicy(str, Enum):
    STRICT_INTERIOR="STRICT_INTERIOR"
    INCLUDE_BOUNDARY="INCLUDE_BOUNDARY"
    RETURN_TOUCH_RELATION="RETURN_TOUCH_RELATION"

class GeocodeStatus(str, Enum):
    UNIQUE_MATCH="UNIQUE_MATCH"
    MULTIPLE_MATCHES="MULTIPLE_MATCHES"
    NO_MATCH="NO_MATCH"
    RESTRICTED_MATCH_EXISTS="RESTRICTED_MATCH_EXISTS"


@dataclass(frozen=True, slots=True)
class SpatialQueryPrincipal:
    principal_id: str
    runtime_mode: OperationRuntimeMode | str
    permissions: frozenset[str]=frozenset()
    def __post_init__(self):
        if not self.principal_id.strip(): raise ValueError("principal_id is required")
        object.__setattr__(self,"runtime_mode",OperationRuntimeMode.parse(self.runtime_mode))
        object.__setattr__(self,"permissions",frozenset(str(x).strip() for x in self.permissions if str(x).strip()))

@dataclass(frozen=True, slots=True)
class SpatialQueryRequest:
    query_code: str
    query_version: int
    runtime_mode: OperationRuntimeMode | str
    parameters: Mapping[str,object]=field(default_factory=dict)
    boundary_policy: BoundaryPolicy=BoundaryPolicy.INCLUDE_BOUNDARY
    limit: int=100
    as_of: datetime | None=None
    def __post_init__(self):
        if not self.query_code.strip(): raise ValueError("query_code is required")
        if self.query_version < 1: raise ValueError("query_version must be positive")
        if not 1 <= self.limit <= 1000: raise ValueError("limit must be between 1 and 1000")
        object.__setattr__(self,"runtime_mode",OperationRuntimeMode.parse(self.runtime_mode))
        object.__setattr__(self,"parameters",MappingProxyType(dict(self.parameters)))
        if self.as_of is not None:
            if self.as_of.tzinfo is None or self.as_of.utcoffset() is None: raise ValueError("as_of must be timezone-aware")
            object.__setattr__(self,"as_of",self.as_of.astimezone(timezone.utc))

@dataclass(frozen=True, slots=True)
class QueryDefinition:
    query_code: str
    query_version: int
    operator_code: str
    input_contract: str
    result_contract: str
    visibility_policy: str
    backend_capability: str
    status: str

@dataclass(frozen=True, slots=True)
class SpatialReadRecord:
    subject_id: str
    family: str
    display_name: str
    runtime_mode: str
    visibility: str
    geometry_id: str | None
    geometry_version: int | None
    read_model_version: int
    longitude: float | None=None
    latitude: float | None=None
    attributes: tuple[tuple[str,object],...]=()
    def __post_init__(self):
        if not self.subject_id or not self.family or not self.display_name: raise ValueError("subject identity, family and display name are required")
        if self.geometry_version is not None and self.geometry_version < 1: raise ValueError("geometry_version must be positive")
        if self.read_model_version < 1: raise ValueError("read_model_version must be positive")
        object.__setattr__(self,"attributes",tuple(sorted(self.attributes,key=lambda x:x[0])))

@dataclass(frozen=True, slots=True)
class SpatialRelationshipResult:
    subject_id: str
    operator: QueryOperator
    object_id: str
    evidence_reference: str | None
    geometry_reference: str | None
    geometry_version: int | None
    status: str

@dataclass(frozen=True, slots=True)
class DistanceMeasurement:
    from_subject_id: str
    to_subject_id: str
    distance_value: float
    distance_unit: str
    measurement_basis: str
    source_crs: str
    governed_crs: str
    def __post_init__(self):
        if self.distance_value < 0: raise ValueError("distance cannot be negative")
        if not self.distance_unit: raise ValueError("distance_unit is required")

@dataclass(frozen=True, slots=True)
class GeocodeMatch:
    subject_id: str
    name_id: str
    subject_family: str
    display_name: str
    scope_reference: str
    visibility: str
    geometry_reference: str | None
    geometry_version: int | None
    runtime_mode: str="production"

@dataclass(frozen=True, slots=True)
class GeocodeResult:
    status: GeocodeStatus
    normalized_query: str
    matches: tuple[GeocodeMatch,...]

@dataclass(frozen=True, slots=True)
class SpatialQueryResult:
    query_code: str
    runtime_mode: str
    records: tuple[object,...]
    result_contract: str
    read_model_version: int
    queried_at: datetime=field(default_factory=lambda:datetime.now(timezone.utc))

__all__=[
    "QueryOperator","BoundaryPolicy","GeocodeStatus","SpatialQueryPrincipal","SpatialQueryRequest","QueryDefinition",
    "SpatialReadRecord","SpatialRelationshipResult","DistanceMeasurement","GeocodeMatch",
    "GeocodeResult","SpatialQueryResult",
]
