"""Materialize deterministic Bundle 20A review artifacts."""
from __future__ import annotations
import csv, json
from collections import Counter
from pathlib import Path
from ._shared import *
from .authoring import author_road_alignments
from .topology import build_network
from .relationships import derive_relationships
from .qualification import qualify_bundle
from .source import source_hashes


def _write_csv(path: Path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows(rows)


def materialize() -> dict[str,int]:
    findings = qualify_bundle()
    if findings: raise ValueError("Bundle20A qualification failed: "+", ".join(findings))
    roads = author_road_alignments(); nodes,segs,conns=build_network(roads); rels=derive_relationships(roads)
    ROAD_POLICY.parent.mkdir(parents=True,exist_ok=True)
    _write_csv(ROAD_POLICY,("policy_id","rule","value"),[
        {"policy_id":"roadnet:policy:001","rule":"CANONICAL_ROAD_SCOPE","value":"FIRST_350_LOCKED_CANONICAL_ROADS_ONLY"},
        {"policy_id":"roadnet:policy:002","rule":"PROVENANCE","value":"NNGLA_SIMULATION_AUTHORED_NOT_FIELD_SURVEYED"},
        {"policy_id":"roadnet:policy:003","rule":"CROSSING_SEMANTICS","value":"GEOMETRIC_CROSSING_DOES_NOT_ASSERT_BRIDGE"},
        {"policy_id":"roadnet:policy:004","rule":"LENGTH_UNIT","value":"METRE_DERIVED_FROM_WGS84_GEOMETRY"},
    ])
    features=[]
    for r in roads:
        features.append({"type":"Feature","properties":{
            "road_id":r.road_id,"road_candidate_id":r.road_candidate_id,"road_name_id":r.road_name_id,"canonical_name":r.canonical_name,
            "road_class_code":r.road_class_code,"region_code":r.region_code,"start_place_id":r.start_place_id,"end_place_id":r.end_place_id,
            "length_m":round(r.length_m,3),"geometry_role_code":r.geometry_role_code,"geometry_reservation_key":r.geometry_reservation_key,
            "geometry_id":"","geometry_id_state":"PENDING_GOVERNED_LIVE_RESERVATION","qualification_status":r.qualification_status,
            "provenance_class":r.provenance_class,"runtime_mode":RUNTIME_MODE,"runtime_effect_scope":r.runtime_effect_scope,"publication_status":"NOT_PUBLISHED",
        },"geometry":{"type":"LineString","coordinates":[[round(x,9),round(y,9)] for x,y in r.coordinates]}})
    ROAD_GEOMETRIES.parent.mkdir(parents=True,exist_ok=True); ROAD_GEOMETRIES.write_text(json.dumps({"type":"FeatureCollection","features":features},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    _write_csv(ROAD_SEGMENTS,("road_segment_id","road_id","source_road_candidate_id","segment_sequence","segment_role","start_node_id","end_node_id","length_m","geometry_reservation_key","geometry_id","geometry_status","addressing_scope_eligible","runtime_effect_scope"),[
        {"road_segment_id":s.road_segment_id,"road_id":s.road_id,"source_road_candidate_id":s.road_candidate_id,"segment_sequence":s.segment_sequence,"segment_role":"WHOLE_AUTHORED_ROAD_EDGE","start_node_id":s.start_node_id,"end_node_id":s.end_node_id,"length_m":f"{s.length_m:.3f}","geometry_reservation_key":s.geometry_reservation_key,"geometry_id":"","geometry_status":"QUALIFIED_PENDING_LIVE_ASSOCIATION","addressing_scope_eligible":str(s.addressing_scope_eligible).lower(),"runtime_effect_scope":EFFECT_SCOPE} for s in segs])
    _write_csv(NETWORK_NODES,("node_id","longitude","latitude","place_id","region_code","node_role","runtime_effect_scope"),[
        {"node_id":n.node_id,"longitude":f"{n.longitude:.9f}","latitude":f"{n.latitude:.9f}","place_id":n.place_id,"region_code":n.region_code,"node_role":n.node_role,"runtime_effect_scope":EFFECT_SCOPE} for n in nodes])
    _write_csv(CONNECTIVITY,("connection_id","node_id","road_segment_id","road_id","endpoint_role","runtime_effect_scope"),[
        {"connection_id":c.connection_id,"node_id":c.node_id,"road_segment_id":c.road_segment_id,"road_id":c.road_id,"endpoint_role":c.endpoint_role,"runtime_effect_scope":EFFECT_SCOPE} for c in conns])
    _write_csv(ROAD_RELATIONSHIPS,("relationship_id","road_id","relationship_type","object_id","evidence_basis","longitude","latitude","runtime_effect_scope"),[
        {"relationship_id":r.relationship_id,"road_id":r.road_id,"relationship_type":r.relationship_type,"object_id":r.object_id,"evidence_basis":r.evidence_basis,"longitude":"" if r.longitude is None else f"{r.longitude:.9f}","latitude":"" if r.latitude is None else f"{r.latitude:.9f}","runtime_effect_scope":EFFECT_SCOPE} for r in rels])
    _write_csv(ASSIGNMENTS,("assignment_candidate_id","subject_type","subject_id","geometry_role_code","geometry_reservation_key","geometry_id","assignment_status","effective_from","runtime_mode","runtime_effect_scope","publication_status"),[
        {"assignment_candidate_id":stable_id("spatialassign:nngla:",r.road_id,"ROAD_ALIGNMENT"),"subject_type":"ROAD","subject_id":r.road_id,"geometry_role_code":GEOMETRY_ROLE,"geometry_reservation_key":r.geometry_reservation_key,"geometry_id":"","assignment_status":"QUALIFIED_PENDING_LIVE_ASSOCIATION","effective_from":BUNDLE_EFFECTIVE_DATE,"runtime_mode":RUNTIME_MODE,"runtime_effect_scope":EFFECT_SCOPE,"publication_status":"NOT_PUBLISHED"} for r in roads])
    _write_csv(QUALIFICATION,("road_id","road_class_code","region_code","geometry_status","topology_status","length_status","overall_status"),[
        {"road_id":r.road_id,"road_class_code":r.road_class_code,"region_code":r.region_code,"geometry_status":"PASS","topology_status":"PASS","length_status":"PASS","overall_status":"PASS"} for r in roads])
    _write_csv(SOURCE_HASHES,("path","sha256","role"),[{"path":p,"sha256":d,"role":"LOCKED_INPUT_OR_BUNDLE20A_POLICY"} for p,d in source_hashes()])
    counts={"roads":len(roads),"segments":len(segs),"nodes":len(nodes),"connections":len(conns),"relationships":len(rels),"junction_nodes":sum(n.node_role=="JUNCTION" for n in nodes)}
    SUMMARY.write_text(json.dumps({"bundle_code":BUNDLE_CODE,"bundle_name":BUNDLE_NAME,"effective_date":BUNDLE_EFFECTIVE_DATE,"counts":counts,"class_counts":dict(Counter(r.road_class_code for r in roads)),"provenance":"NNGLA_SIMULATION_AUTHORED_NOT_FIELD_SURVEYED","publication_status":"NOT_PUBLISHED"},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return counts

if __name__ == "__main__": print(materialize())
