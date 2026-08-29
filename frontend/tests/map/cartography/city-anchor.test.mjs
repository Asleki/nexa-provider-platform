import test from "node:test";
import assert from "node:assert/strict";
import {
  OFFICIAL_NOVEGEO_CITY_IDS,
  assertPublishedNoveGeoCitySubset,
  createNoveGeoCityLabelCandidate,
} from "../../../src/map/cartography/city-anchor.js";

function item(id="NG-ADM-000170", index=7) {
  return {
    subjectId:id,family:"ADMINISTRATIVE_AREA",displayName:"Port Meridian",
    publicationReference:"city-publication:nngla:port-meridian",publicEligible:true,mapRenderable:true,
    geometryId:`city-geometry:nngla:${id}:v1`,geometryVersion:1,geometryType:"POLYGON",crsCode:"NG-CRS-EPSG4326",
    geometry:{type:"Polygon",coordinates:[[[42.8,0.1],[43.3,0.1],[43.3,0.7],[42.8,0.1]]]},
    runtimeEffectScope:"SHARED_REFERENCE",classificationScheme:"NNGLA_ADMIN_TYPE",classificationCode:"CITY",
    parentRegionId:`NG-ADM-${String(index+1).padStart(6,"0")}`,
    labelPoint:{type:"Point",coordinates:[43.0,0.35]},labelAnchorKind:"DERIVED_PRESENTATION",
    labelPointAlgorithmId:"algorithm:nngla:city-label-point-on-surface:epsg4326",labelPointAlgorithmVersion:1,
  };
}

test("CITY adapter reuses ADMIN_CITY and authoritative CITY geometry identity",()=>{
  const candidate=createNoveGeoCityLabelCandidate(item(),{readRuntime:"simulation"});
  assert.equal(candidate.labelClass,"ADMIN_CITY");
  assert.equal(candidate.runtimeMode,"shared_reference");
  assert.equal(candidate.anchor.kind,"DERIVED_PRESENTATION");
  assert.equal(candidate.anchor.sourceGeometryId,"city-geometry:nngla:NG-ADM-000170:v1");
});

test("published CITY set is intentionally incremental from zero through eight",()=>{
  assert.equal(assertPublishedNoveGeoCitySubset([]).length,0);
  assert.deepEqual(assertPublishedNoveGeoCitySubset([item()]).map(x=>x.subjectId),["NG-ADM-000170"]);
  const all=OFFICIAL_NOVEGEO_CITY_IDS.map((id,index)=>item(id,index));
  assert.equal(assertPublishedNoveGeoCitySubset(all).length,8);
});

test("unknown or duplicate CITY identity fails closed",()=>{
  assert.throws(()=>assertPublishedNoveGeoCitySubset([{...item(),subjectId:"NG-ADM-999999"}]),/unknown identity/);
  assert.throws(()=>assertPublishedNoveGeoCitySubset([item(),item()]),/duplicate identity/);
});
