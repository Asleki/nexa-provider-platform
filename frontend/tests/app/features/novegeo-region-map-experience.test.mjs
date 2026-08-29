import test from "node:test";
import assert from "node:assert/strict";
import { installNoveGeoRegionMapExperience } from "../../../src/app/features/novegeo-region-map-experience.js";
import { OFFICIAL_NOVEGEO_REGION_IDS } from "../../../src/map/cartography/region-anchor.js";

function region(id,index){
  const x=30+index;
  return {
    subjectId:id,family:"ADMINISTRATIVE_AREA",displayName:`Region ${index+1}`,
    publicationReference:`publication:nngla:region:${index+1}`,publicEligible:true,mapRenderable:true,
    geometryId:`NG-GEO-${String(200001+index).padStart(6,"0")}`,geometryVersion:1,geometryType:"POLYGON",crsCode:"NG-CRS-EPSG4326",
    geometry:{type:"Polygon",coordinates:[[[x,0],[x+.5,0],[x+.5,.5],[x,0]]]},runtimeEffectScope:"SHARED_REFERENCE",
    classificationScheme:"NNGLA_ADMIN_TYPE",classificationCode:"REGION",
    labelPoint:{type:"Point",coordinates:[x+.25,.25]},labelPointAlgorithmId:"algorithm:nngla:region-label-point-on-surface:epsg4326",labelPointAlgorithmVersion:1,
  };
}

function documentFixture(){
  const canvas={};
  const viewport={querySelector(selector){return selector==="[data-role='novegeo-map-canvas']"?canvas:null;}};
  const page={dataset:{},querySelector(selector){return selector==="[data-role='future-map-viewport']"?viewport:null;}};
  return {page,querySelector(selector){if(selector===".novegeo-feature-page")return page;if(selector==="[data-role='future-map-viewport']")return viewport;return null;}};
}

test("experience requests only existing ADMINISTRATIVE_AREA family and mounts exactly eight REGIONs",async()=>{
  const doc=documentFixture();
  const win={location:{protocol:"http:",hostname:"127.0.0.1"},addEventListener(){},removeEventListener(){}};
  const boundary={extent:{minLongitude:29,minLatitude:-8,maxLongitude:45,maxLatitude:8}};
  const items=OFFICIAL_NOVEGEO_REGION_IDS.map(region);
  let readArgs=null,mounted=null;
  const experience=installNoveGeoRegionMapExperience({
    documentRef:doc,windowRef:win,fetchRef:()=>{},apiBaseUrl:"http://127.0.0.1:8000",
    createBoundaryClientRef:()=>({getActive:async()=>boundary}),
    createMapClientRef:()=>({readViewport:async(bounds,options)=>{readArgs={bounds,options};return {authorityId:"authority:nngla",countryId:"country:novegeo",readRuntime:"simulation",items,semanticChecksum:"a".repeat(64)};}}),
    mountOverlayRef:(_document,options)=>{mounted=options;return {status:"RENDERED",disconnect(){}};},
  });
  const result=await experience.refresh();
  assert.equal(result.status,"RENDERED");
  assert.equal(result.regionCount,8);
  assert.deepEqual(readArgs.options.families,["ADMINISTRATIVE_AREA"]);
  assert.equal(readArgs.options.limit,2000);
  assert.equal(mounted.regionItems.length,8);
  assert.equal(doc.page.dataset.novegeoRegionMapStatus,"READY");
  assert.equal(doc.page.dataset.novegeoRegionMapCount,"8");
  experience.disconnect();
});

test("experience fails closed when endpoint does not deliver the complete official REGION set",async()=>{
  const doc=documentFixture();
  const win={location:{protocol:"http:",hostname:"127.0.0.1"},addEventListener(){},removeEventListener(){}};
  const experience=installNoveGeoRegionMapExperience({
    documentRef:doc,windowRef:win,fetchRef:()=>{},apiBaseUrl:"http://127.0.0.1:8000",
    createBoundaryClientRef:()=>({getActive:async()=>({extent:{minLongitude:29,minLatitude:-8,maxLongitude:45,maxLatitude:8}})}),
    createMapClientRef:()=>({readViewport:async()=>({authorityId:"authority:nngla",countryId:"country:novegeo",readRuntime:"simulation",items:[region("NG-ADM-000001",0)]})}),
    mountOverlayRef:()=>{throw new Error("must not mount");},
  });
  const result=await experience.refresh();
  assert.equal(result.status,"DEGRADED");
  assert.match(result.reason,/expected 8, received 1/);
  assert.equal(doc.page.dataset.novegeoRegionMapStatus,"DEGRADED");
  experience.disconnect();
});
