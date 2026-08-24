import test from "node:test";import assert from "node:assert/strict";
import {normalizeNationalMapPayload} from "../../../src/map/nngla/national-map-contracts.js";
const payload={authorityId:"authority:nngla",countryId:"country:novegeo",readRuntime:"simulation",items:[{subjectId:"NG-PLC-000001",family:"PLACE",publicationReference:"publication:nngla:1",publicEligible:true,mapRenderable:true,geometryId:"NG-GEO-000001",geometryVersion:1,crsCode:"NG-CRS-EPSG4326",geometry:{type:"Point",coordinates:[31,-18]}}]};
test("Bundle 22B accepts only public renderable canonical map features",()=>{assert.equal(normalizeNationalMapPayload(payload).items[0].subjectId,"NG-PLC-000001");});
test("Bundle 22B rejects candidate/non-public payloads",()=>{assert.throws(()=>normalizeNationalMapPayload({...payload,items:[{...payload.items[0],publicEligible:false}]}));});
