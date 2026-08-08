"""P005.3 governed river, lake, drainage and confluence authority."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json, math
from .geometry import canonical_sha256

class HydrologyValidationError(ValueError):
    pass

@dataclass(frozen=True, slots=True)
class HydrologyQualification:
    qualification_id: str
    decision: str
    river_count: int
    lake_count: int
    drainage_network_count: int
    content_sha256: str


def load_hydrology_dataset(path: Path) -> dict[str, Any]:
    try:
        value=json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:
        raise HydrologyValidationError(f"cannot read hydrology dataset: {exc}") from exc
    if not isinstance(value,dict):
        raise HydrologyValidationError("hydrology dataset must be an object")
    return value


def _point(value: Any, field: str) -> tuple[float,float]:
    if not isinstance(value,dict):
        raise HydrologyValidationError(f"{field} must be an object")
    vals=[value.get("longitude"),value.get("latitude")]
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in vals):
        raise HydrologyValidationError(f"{field} must contain finite longitude/latitude")
    return float(vals[0]),float(vals[1])


def _coord_pair(value: Any, field: str) -> tuple[float,float]:
    if not isinstance(value,list) or len(value)!=2 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in value):
        raise HydrologyValidationError(f"{field} must contain finite longitude/latitude")
    return float(value[0]),float(value[1])


def validate_hydrology_dataset(value: dict[str, Any]) -> dict[str, Any]:
    required={"hydrologyId":"hydrology:novegeo:surface-water","hydrologyVersion":1,"datasetId":"dataset:novegeo:hydrology:surface-water","datasetVersion":1,"boundaryId":"boundary:novegeo:sovereign","boundaryVersion":2,"terrainDatasetId":"dataset:novegeo:terrain:elevation","terrainDatasetVersion":1,"runtimeMode":"shared_reference","visibility":"public"}
    for k,e in required.items():
        if value.get(k)!=e:
            raise HydrologyValidationError(f"{k} expected {e!r}, got {value.get(k)!r}")
    model=value.get("cartographicModel",{})
    if model.get("anonymousFeatureIdentity") is not True or model.get("featureNamingAuthority")!="deferred":
        raise HydrologyValidationError("hydrology feature naming must remain deferred")
    if model.get("riverTopology")!="exact_shared_coordinate_confluences":
        raise HydrologyValidationError("river topology must use exact shared-coordinate confluences")
    if model.get("lakeConnectivity")!="closed_basins_without_distributaries":
        raise HydrologyValidationError("v001 lakes must remain without distributaries")

    networks=value.get("drainageNetworks"); rivers=value.get("rivers"); lakes=value.get("lakes"); junctions=value.get("junctions")
    if not isinstance(networks,list) or len(networks)<3: raise HydrologyValidationError("at least three drainage networks are required")
    if not isinstance(rivers,list) or len(rivers)<4: raise HydrologyValidationError("at least four rivers are required")
    if not isinstance(lakes,list) or len(lakes)<2: raise HydrologyValidationError("at least two lakes are required")
    if not isinstance(junctions,list) or not junctions: raise HydrologyValidationError("connected river topology requires confluence junctions")

    network_ids=set()
    for n in networks:
        nid=n.get("drainageNetworkId")
        if not isinstance(nid,str) or not nid.startswith("drainage:novegeo:d") or nid in network_ids: raise HydrologyValidationError("drainage IDs must be anonymous, unique and namespaced")
        if "name" in n: raise HydrologyValidationError("drainage names are deferred to a future naming authority")
        network_ids.add(nid)

    river_ids=set(); river_by_id={}; lake_ids=set()
    for river in rivers:
        rid=river.get("riverId")
        if not isinstance(rid,str) or not rid.startswith("river:novegeo:r") or rid in river_ids: raise HydrologyValidationError("river IDs must be anonymous, unique and namespaced")
        if "name" in river: raise HydrologyValidationError("river names are deferred to a future naming authority")
        river_ids.add(rid); river_by_id[rid]=river
        if river.get("drainageNetworkId") not in network_ids: raise HydrologyValidationError("river drainage network is unknown")
        if river.get("riverClass") not in {"tributary","secondary","principal"}: raise HydrologyValidationError("riverClass is invalid")
        if river.get("streamOrder") not in {1,2,3}: raise HydrologyValidationError("streamOrder is invalid")
        _point(river.get("referencePoint"),"river referencePoint")
        geom=river.get("geometry",{}); coords=geom.get("coordinates"); profile=river.get("elevationProfileMeters")
        if geom.get("type")!="LineString" or not isinstance(coords,list) or len(coords)<20: raise HydrologyValidationError("river geometry must be a sufficiently densified LineString")
        if not isinstance(profile,list) or len(profile)!=len(coords): raise HydrologyValidationError("river elevation profile must align with geometry")
        if any(not isinstance(v,int) for v in profile): raise HydrologyValidationError("river elevation profile must use integer metres")
        if any(profile[i+1]>=profile[i] for i in range(len(profile)-1)): raise HydrologyValidationError("river flow must descend from source to outlet")
        for c in coords: _coord_pair(c,"river coordinate")

    for lake in lakes:
        lid=lake.get("lakeId")
        if not isinstance(lid,str) or not lid.startswith("lake:novegeo:l") or lid in lake_ids: raise HydrologyValidationError("lake IDs must be anonymous, unique and namespaced")
        if "name" in lake: raise HydrologyValidationError("lake names are deferred to a future naming authority")
        lake_ids.add(lid)
        if lake.get("drainageNetworkId") not in network_ids: raise HydrologyValidationError("lake drainage network is unknown")
        if lake.get("geometry",{}).get("type")!="Polygon": raise HydrologyValidationError("lake geometry must be Polygon")
        _point(lake.get("referencePoint"),"lake referencePoint")
        if lake.get("hydrologicRole")!="closed_basin_lake" or lake.get("surfaceOutlet")!="none_declared":
            raise HydrologyValidationError("v001 lakes must remain closed-basin features without distributaries")

    junction_ids=set(); junction_by_id={}
    for junction in junctions:
        jid=junction.get("junctionId")
        if not isinstance(jid,str) or not jid.startswith("junction:novegeo:j") or jid in junction_ids: raise HydrologyValidationError("junction IDs must be anonymous, unique and namespaced")
        if junction.get("junctionType")!="confluence": raise HydrologyValidationError("junctionType must be confluence")
        _point(junction.get("coordinate"),"junction coordinate")
        receiving=junction.get("receivingRiverId"); incoming=junction.get("incomingRiverIds")
        if receiving not in river_ids or not isinstance(incoming,list) or not incoming or any(r not in river_ids for r in incoming): raise HydrologyValidationError("junction river references are invalid")
        if receiving in incoming: raise HydrologyValidationError("receiving river cannot also be incoming")
        junction_ids.add(jid); junction_by_id[jid]=junction

    # Exact topology: tributary/secondary endpoint == junction coordinate == a receiving-channel vertex.
    for river in rivers:
        downstream_jid=river.get("downstreamJunctionId")
        downstream_rid=river.get("downstreamRiverId")
        if downstream_jid is None:
            if river.get("riverClass")!="principal" or river.get("outletType")!="coast": raise HydrologyValidationError("only principal outlet river may omit downstream junction")
            continue
        if downstream_jid not in junction_by_id or downstream_rid not in river_by_id: raise HydrologyValidationError("river downstream topology reference is unknown")
        junction=junction_by_id[downstream_jid]
        if river["riverId"] not in junction["incomingRiverIds"] or downstream_rid!=junction["receivingRiverId"]: raise HydrologyValidationError("river downstream topology disagrees with junction authority")
        jc=(float(junction["coordinate"]["longitude"]),float(junction["coordinate"]["latitude"]))
        endpoint=tuple(map(float,river["geometry"]["coordinates"][-1]))
        receiving_points={tuple(map(float,c)) for c in river_by_id[downstream_rid]["geometry"]["coordinates"]}
        if endpoint!=jc or jc not in receiving_points: raise HydrologyValidationError("confluence must use an exact shared coordinate")
        receiving=river_by_id[downstream_rid]
        idx=[tuple(map(float,c)) for c in receiving["geometry"]["coordinates"]].index(jc)
        if river["outletElevationMeters"]!=receiving["elevationProfileMeters"][idx]: raise HydrologyValidationError("confluence elevation must match receiving river")

    for n in networks:
        if any(x not in river_ids for x in n.get("riverIds",[])) or any(x not in lake_ids for x in n.get("lakeIds",[])) or any(x not in junction_ids for x in n.get("junctionIds",[])): raise HydrologyValidationError("drainage membership references unknown features")
    # Explicit lake safety: no river in v001 may claim a lake downstream, and closed-basin networks contain no rivers/junctions.
    for n in networks:
        if n.get("outletType")=="closed_basin" and (n.get("riverIds") or n.get("junctionIds")): raise HydrologyValidationError("closed-basin lake networks must not contain river/distributary topology")

    expected=value.get("contentSha256"); unsigned=dict(value); unsigned.pop("contentSha256",None)
    if not isinstance(expected,str) or canonical_sha256(unsigned)!=expected: raise HydrologyValidationError("hydrology contentSha256 mismatch")
    return value


def qualify_hydrology_dataset(path: Path) -> HydrologyQualification:
    value=validate_hydrology_dataset(load_hydrology_dataset(path))
    return HydrologyQualification("qualification:novegeo:hydrology:v001","qualified",len(value["rivers"]),len(value["lakes"]),len(value["drainageNetworks"]),value["contentSha256"])
