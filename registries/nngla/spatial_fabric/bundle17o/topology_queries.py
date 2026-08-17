"""Query-operator layer kept distinct from persisted Bundle 17C relationship vocabulary."""
from __future__ import annotations
from dataclasses import dataclass
from .contracts import QueryOperator, SpatialRelationshipResult

PERSISTED_RELATIONSHIP_MAPPING={
    QueryOperator.CONTAINS:"CONTAINS", QueryOperator.WITHIN:"WITHIN",
    QueryOperator.INTERSECTS:"INTERSECTS", QueryOperator.CROSSES:"CROSSES",
    QueryOperator.TOUCHES:"TOUCHES", QueryOperator.ADJACENT:"ADJACENT_TO",
    QueryOperator.FRONTS:"FRONTS", QueryOperator.CONNECTED_TO:"CONNECTED_TO",
}
NON_PERSISTED_MEASUREMENT_OPERATORS=frozenset({QueryOperator.NEAREST,QueryOperator.DISTANCE})

@dataclass(frozen=True,slots=True)
class RelationshipEvidence:
    subject_id: str
    persisted_relationship_type: str
    object_id: str
    evidence_reference: str
    geometry_reference: str | None=None
    geometry_version: int | None=None
    runtime_mode: str="production"
    visibility: str="PUBLIC"

class MemoryTopologyBackend:
    def __init__(self,evidence=()): self.evidence=tuple(evidence)
    def query(self,operator: QueryOperator,subject_id: str,object_id: str|None=None,*,runtime_mode="production",allow_restricted=False,limit=100):
        if operator not in PERSISTED_RELATIONSHIP_MAPPING: raise ValueError("operator requires measurement/query backend rather than persisted relationship evidence")
        persisted=PERSISTED_RELATIONSHIP_MAPPING[operator]
        rows=[]
        for e in self.evidence:
            if e.runtime_mode!=runtime_mode or (e.visibility!="PUBLIC" and not allow_restricted): continue
            if e.subject_id!=subject_id or e.persisted_relationship_type!=persisted: continue
            if object_id is not None and e.object_id!=object_id: continue
            rows.append(SpatialRelationshipResult(e.subject_id,operator,e.object_id,e.evidence_reference,e.geometry_reference,e.geometry_version,"MATCH"))
        return tuple(rows[:limit])
__all__=["PERSISTED_RELATIONSHIP_MAPPING","NON_PERSISTED_MEASUREMENT_OPERATORS","RelationshipEvidence","MemoryTopologyBackend"]
