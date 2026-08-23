"""Adapter over the locked P006.7.9 public visibility rules; no policy rewrite."""
from __future__ import annotations
from registries.nngla.publication_policy15d import decide_place_visibility,decide_administrative_area_visibility,decide_feature_visibility,decide_road_visibility
from .contracts import PublicationCandidate,PublicationDecision
from ._shared import stable_id,TARGET_RUNTIME

def decide(candidate:PublicationCandidate, *, published_through_gate:bool=False, live_geometry_id:str|None=None, live_name_status:str|None=None, live_geometry_publication_status:str|None=None):
    geom=live_geometry_id if live_geometry_id is not None else candidate.geometry_reference
    name=live_name_status if live_name_status is not None else candidate.naming_status
    gpub=live_geometry_publication_status if live_geometry_publication_status is not None else candidate.geometry_publication_status
    if candidate.record_family=='PLACE': d=decide_place_visibility(naming_status_code=name,spatial_assignment_status=candidate.lifecycle_status,published_through_gate=published_through_gate)
    elif candidate.record_family=='ADMINISTRATIVE_AREA': d=decide_administrative_area_visibility(lifecycle_status=candidate.naming_status,boundary_status=candidate.lifecycle_status,geometry_reference=geom,published_through_gate=published_through_gate)
    elif candidate.record_family=='ROAD': d=decide_road_visibility(planning_status=candidate.lifecycle_status,geometry_status=candidate.spatial_status,geometry_reference=geom,published_through_gate=published_through_gate)
    else: d=decide_feature_visibility(naming_status_code=name,publication_status=gpub,published_through_gate=published_through_gate)
    if d.public_eligible:
        pid=stable_id('publication:nngla:',candidate.subject_id,TARGET_RUNTIME,1)
        return PublicationDecision(candidate.subject_id,candidate.record_family,'PUBLIC',(),d.map_renderable,pid)
    return PublicationDecision(candidate.subject_id,candidate.record_family,'BLOCKED',d.reasons,False,'')
