import csv,hashlib,json
from pathlib import Path
import registries.nngla.town_footprint_realization.source as source_module
from registries.nngla.town_footprint_realization.source import load_town_sources

def test_bundle19a_multi_artifact_shape_contract(tmp_path,monkeypatch):
    refs=[]; features=[]
    for p in range(24):
        parent_code=f"M{p:02d}"; parent_id=f"NG-PLC-{900000+p:06d}"; refs.append({"source_place_code":parent_code,"place_id":parent_id,"canonical_name":f"M{p}","place_type_code":"MUNICIPALITY","region_code":"NGR-01","parent_source_place_code":""})
        for j in range(5):
            idx=p*5+j+1; pid=f"NG-PLC-{idx:06d}"; code=f"T{idx:03d}"; name=f"Town {idx}"; refs.append({"source_place_code":code,"place_id":pid,"canonical_name":name,"place_type_code":"TOWN","region_code":"NGR-01","parent_source_place_code":parent_code})
            features.append({"type":"Feature","properties":{"place_id":pid,"canonical_name":name,"source_place_code":code,"place_type_code":"TOWN","region_code":"NGR-01","crs_code":"NG-CRS-EPSG4326","runtime_effect_scope":"SHARED_REFERENCE","geometry_role_code":"SETTLEMENT_FOOTPRINT","qualification_status":"QUALIFIED_CANDIDATE_NOT_LEGAL_BOUNDARY","legal_boundary_status":"NOT_ADMINISTRATIVE_OR_LEGAL_BOUNDARY","source_basis":source_module.SOURCE_BASIS},"geometry":{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,0]]]}})
    for i in range(700-len(refs)): refs.append({"source_place_code":f"X{i}","place_id":f"NG-PLC-{700000+i:06d}","canonical_name":f"X{i}","place_type_code":"SUBURB","region_code":"NGR-01","parent_source_place_code":""})
    for i in range(419-len(features)): features.append({"type":"Feature","properties":{"place_id":f"NG-PLC-{500000+i:06d}","place_type_code":"SUBURB"},"geometry":{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,0]]]}})
    r=tmp_path/"refs.csv"; f=tmp_path/"foot.geojson"; s=tmp_path/"summary.json"
    fields=["source_place_code","place_id","canonical_name","place_type_code","region_code","parent_source_place_code"]
    with r.open("w",newline="",encoding="utf-8") as h:
        w=csv.DictWriter(h,fieldnames=fields); w.writeheader(); w.writerows(refs)
    f.write_text(json.dumps({"type":"FeatureCollection","features":features}),encoding="utf-8")
    s.write_text(json.dumps({"source_dataset_id":"dataset:novegeo:place-spatial-association","source_dataset_version":"1","runtime_effect_scope":"SHARED_REFERENCE","qualification_status":"PASS","counts":{"settlement_footprints":419}}),encoding="utf-8")
    monkeypatch.setattr(source_module,"REFERENCE_SHA256",hashlib.sha256(r.read_bytes()).hexdigest()); monkeypatch.setattr(source_module,"FOOTPRINT_SHA256",hashlib.sha256(f.read_bytes()).hexdigest())
    rows=load_town_sources(f,r,s); assert len(rows)==120; assert len({x.parent_source_place_code for x in rows})==24
