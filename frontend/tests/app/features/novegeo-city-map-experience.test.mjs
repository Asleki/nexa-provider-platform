import test from "node:test";
import assert from "node:assert/strict";
import { installNoveGeoCityMapExperience } from "../../../src/app/features/novegeo-city-map-experience.js";

function city(){return {subjectId:"NG-ADM-000170",family:"ADMINISTRATIVE_AREA",displayName:"Port Meridian",publicationReference:"city-publication:nngla:port-meridian",publicEligible:true,mapRenderable:true,geometryId:"city-geometry:nngla:NG-ADM-000170:v1",geometryVersion:1,geometryType:"POLYGON",crsCode:"NG-CRS-EPSG4326",geometry:{type:"Polygon",coordinates:[[[42.8,0.1],[43.3,0.1],[43.3,0.7],[42.8,0.1]]]},runtimeEffectScope:"SHARED_REFERENCE",classificationScheme:"NNGLA_ADMIN_TYPE",classificationCode:"CITY",parentRegionId:"NG-ADM-000008",labelPoint:{type:"Point",coordinates:[43.0,0.35]},labelPointAlgorithmId:"algorithm:nngla:city-label-point-on-surface:epsg4326",labelPointAlgorithmVersion:1};}
function documentFixture(){const canvas={};const viewport={querySelector(selector){return selector==="[data-role='novegeo-map-canvas']"?canvas:null;}};const page={dataset:{},querySelector(selector){return selector==="[data-role='future-map-viewport']"?viewport:null;}};return {page,querySelector(selector){if(selector===".novegeo-feature-page")return page;if(selector==="[data-role='future-map-viewport']")return viewport;return null;}};}

test("experience requests existing ADMINISTRATIVE_AREA family and mounts one Port Meridian pilot",async()=>{
  const doc=documentFixture(); const win={location:{protocol:"http:",hostname:"127.0.0.1"},addEventListener(){},removeEventListener(){}};
  let readArgs=null,mounted=null;
  const experience=installNoveGeoCityMapExperience({documentRef:doc,windowRef:win,fetchRef:()=>{},apiBaseUrl:"http://127.0.0.1:8000",createBoundaryClientRef:()=>({getActive:async()=>({extent:{minLongitude:29,minLatitude:-8,maxLongitude:45,maxLatitude:8}})}),createMapClientRef:()=>({readViewport:async(bounds,options)=>{readArgs={bounds,options};return {readRuntime:"simulation",items:[city()],semanticChecksum:"a".repeat(64)};}}),mountOverlayRef:(_d,options)=>{mounted=options;return {status:"RENDERED",disconnect(){}};}});
  const result=await experience.refresh();
  assert.equal(result.status,"RENDERED"); assert.equal(result.cityCount,1);
  assert.deepEqual(readArgs.options.families,["ADMINISTRATIVE_AREA"]); assert.equal(readArgs.options.limit,2000);
  assert.equal(mounted.cityItems[0].subjectId,"NG-ADM-000170"); assert.equal(doc.page.dataset.novegeoCityMapStatus,"READY");
  experience.disconnect();
});

test("experience permits zero published CITY records",async()=>{
  const doc=documentFixture(); const win={location:{protocol:"http:",hostname:"127.0.0.1"},addEventListener(){},removeEventListener(){}};
  const experience=installNoveGeoCityMapExperience({documentRef:doc,windowRef:win,fetchRef:()=>{},apiBaseUrl:"http://127.0.0.1:8000",createBoundaryClientRef:()=>({getActive:async()=>({extent:{minLongitude:29,minLatitude:-8,maxLongitude:45,maxLatitude:8}})}),createMapClientRef:()=>({readViewport:async()=>({readRuntime:"simulation",items:[]})}),mountOverlayRef:()=>({status:"RENDERED",disconnect(){}})});
  const result=await experience.refresh(); assert.equal(result.status,"RENDERED"); assert.equal(result.cityCount,0); experience.disconnect();
});
