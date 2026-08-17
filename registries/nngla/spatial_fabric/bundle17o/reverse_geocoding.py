"""Reference reverse-geocoding stack over supplied authoritative polygon rings."""
from __future__ import annotations
from dataclasses import dataclass
from .contracts import BoundaryPolicy,SpatialReadRecord
@dataclass(frozen=True,slots=True)
class PolygonReadRecord:
    record: SpatialReadRecord
    ring: tuple[tuple[float,float],...]
    hierarchy_rank: int
def _on_segment(x,y,x1,y1,x2,y2,eps=1e-12):
    cross=(x-x1)*(y2-y1)-(y-y1)*(x2-x1)
    if abs(cross)>eps:return False
    return min(x1,x2)-eps<=x<=max(x1,x2)+eps and min(y1,y2)-eps<=y<=max(y1,y2)+eps
def _contains(ring,x,y,boundary_policy):
    if len(ring)<3:return False
    pts=ring if ring[0]==ring[-1] else ring+(ring[0],)
    for a,b in zip(pts,pts[1:]):
        if _on_segment(x,y,a[0],a[1],b[0],b[1]):
            return boundary_policy is BoundaryPolicy.INCLUDE_BOUNDARY
    inside=False
    for (x1,y1),(x2,y2) in zip(pts,pts[1:]):
        if ((y1>y)!=(y2>y)) and x < (x2-x1)*(y-y1)/(y2-y1)+x1: inside=not inside
    return inside
class MemoryReverseGeocoder:
    def __init__(self,polygons=()): self.polygons=tuple(polygons)
    def reverse(self,longitude,latitude,*,runtime_mode,boundary_policy=BoundaryPolicy.INCLUDE_BOUNDARY,allow_restricted=False,limit=100):
        rows=[p for p in self.polygons if p.record.runtime_mode==runtime_mode and (allow_restricted or p.record.visibility=="PUBLIC") and _contains(p.ring,longitude,latitude,boundary_policy)]
        rows.sort(key=lambda p:(p.hierarchy_rank,p.record.family,p.record.subject_id))
        return tuple(p.record for p in rows[:limit])
__all__=["PolygonReadRecord","MemoryReverseGeocoder"]
