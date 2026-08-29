import test from "node:test";
import assert from "node:assert/strict";
import {
  OFFICIAL_NOVEGEO_REGION_IDS,
  assertOfficialNoveGeoRegionSet,
  createNoveGeoRegionLabelCandidate,
} from "../../../src/map/cartography/region-anchor.js";

function item(id="NG-ADM-000001") {
  return {
    subjectId:id,family:"ADMINISTRATIVE_AREA",displayName:"Region",
    publicationReference:"publication:nngla:region",publicEligible:true,mapRenderable:true,
    geometryId:"NG-GEO-123456",geometryVersion:1,geometryType:"POLYGON",crsCode:"NG-CRS-EPSG4326",
    geometry:{type:"Polygon",coordinates:[[[30,0],[31,0],[31,1],[30,0]]]},
    runtimeEffectScope:"SHARED_REFERENCE",classificationScheme:"NNGLA_ADMIN_TYPE",classificationCode:"REGION",
    labelPoint:{type:"Point",coordinates:[30.5,0.5]},labelAnchorKind:"DERIVED_PRESENTATION",
    labelPointAlgorithmId:"algorithm:nngla:region-label-point-on-surface:epsg4326",labelPointAlgorithmVersion:1,
  };
}

test("REGION adapter reuses ADMIN_REGION and source geometry identity",()=>{
  const candidate=createNoveGeoRegionLabelCandidate(item(),{readRuntime:"simulation"});
  assert.equal(candidate.labelClass,"ADMIN_REGION");
  assert.equal(candidate.runtimeMode,"shared_reference");
  assert.equal(candidate.anchor.kind,"DERIVED_PRESENTATION");
  assert.equal(candidate.anchor.sourceGeometryId,"NG-GEO-123456");
  assert.equal(candidate.anchor.algorithmId,"algorithm:nngla:region-label-point-on-surface:epsg4326");
});

test("official set is exactly the eight governed REGION identities",()=>{
  const items=OFFICIAL_NOVEGEO_REGION_IDS.map(item);
  const result=assertOfficialNoveGeoRegionSet(items);
  assert.equal(result.length,8);
  assert.deepEqual(result.map(x=>x.subjectId),[...OFFICIAL_NOVEGEO_REGION_IDS]);
});

test("incomplete official set fails closed",()=>{
  assert.throws(()=>assertOfficialNoveGeoRegionSet([item()]),/expected 8, received 1/);
});

test("unexpected REGION identity fails the exact-set gate",()=>{
  const items=OFFICIAL_NOVEGEO_REGION_IDS.map(item);
  items.push({...item("NG-ADM-000001"),subjectId:"NG-ADM-999999"});
  assert.throws(()=>assertOfficialNoveGeoRegionSet(items),/expected 8, received 9/);
});
