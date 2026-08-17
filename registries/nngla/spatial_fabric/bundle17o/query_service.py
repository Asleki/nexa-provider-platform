"""Framework-neutral NNGLA spatial query service."""
from __future__ import annotations
from .contracts import QueryOperator,SpatialQueryPrincipal,SpatialQueryRequest,SpatialQueryResult
from .query_catalogue import get_query_definition
from .distance_queries import distance_between,nearest

class SpatialQueryService:
    RESTRICTED_READ_PERMISSION="nngla.read.restricted"
    def __init__(self,read_repository,*,topology_backend=None,geocoder=None,reverse_geocoder=None,read_model_version=1):
        self.read_repository=read_repository; self.topology_backend=topology_backend
        self.geocoder=geocoder; self.reverse_geocoder=reverse_geocoder; self.read_model_version=read_model_version
    def execute(self,request: SpatialQueryRequest,principal: SpatialQueryPrincipal|None=None):
        if request.as_of is not None:
            raise NotImplementedError("historical as_of spatial querying is reserved for a later additive milestone")
        if principal is not None and principal.runtime_mode is not request.runtime_mode:
            raise PermissionError("query principal runtime does not match requested runtime")
        allow_restricted=principal is not None and self.RESTRICTED_READ_PERMISSION in principal.permissions
        definition=get_query_definition(request.query_code,request.query_version)
        rt=request.runtime_mode.value; p=request.parameters
        code=definition.query_code
        if code=="FIND_BY_CANONICAL_ID":
            r=self.read_repository.get(str(p["subject_id"]),runtime_mode=rt,allow_restricted=allow_restricted); records=() if r is None else (r,)
        elif code=="GEOCODE":
            if self.geocoder is None: raise RuntimeError("geocoder backend required")
            records=(self.geocoder.geocode(str(p["text"]),scope_reference=p.get("scope_reference"),runtime_mode=rt,allow_restricted=allow_restricted,limit=request.limit),)
        elif code=="REVERSE_GEOCODE":
            if self.reverse_geocoder is None: raise RuntimeError("reverse geocoder backend required")
            records=self.reverse_geocoder.reverse(float(p["longitude"]),float(p["latitude"]),runtime_mode=rt,boundary_policy=request.boundary_policy,allow_restricted=allow_restricted,limit=request.limit)
        elif definition.operator_code in {"NEAREST","DISTANCE"}:
            origin=self.read_repository.get(str(p["subject_id"]),runtime_mode=rt,allow_restricted=allow_restricted)
            if origin is None: records=()
            elif definition.operator_code=="DISTANCE":
                target=self.read_repository.get(str(p["object_id"]),runtime_mode=rt,allow_restricted=allow_restricted)
                records=() if target is None else (distance_between(origin,target),)
            else:
                family=str(p["family"])
                candidates=self.read_repository.list_family(family,runtime_mode=rt,allow_restricted=allow_restricted)
                records=nearest(origin,candidates,limit=request.limit)
        else:
            if self.topology_backend is None: raise RuntimeError("topology backend required")
            op=QueryOperator(definition.operator_code)
            records=self.topology_backend.query(op,str(p["subject_id"]),str(p["object_id"]) if p.get("object_id") is not None else None,runtime_mode=rt,allow_restricted=allow_restricted,limit=request.limit)
        return SpatialQueryResult(code,rt,tuple(records),definition.result_contract,self.read_model_version)
__all__=["SpatialQueryService"]
