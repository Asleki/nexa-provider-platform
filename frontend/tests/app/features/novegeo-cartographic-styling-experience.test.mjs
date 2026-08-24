import test from "node:test";
import assert from "node:assert/strict";
import {installNoveGeoCartographicStylingExperience} from "../../../src/app/features/novegeo-cartographic-styling-experience.js";

function fixture(){
  const canvas={};
  const viewport={querySelector(sel){return sel.includes("novegeo-map-canvas")?canvas:null;}};
  const page={dataset:{},querySelector(sel){return sel.includes("future-map-viewport")?viewport:null;}};
  const head={children:[],appendChild(node){this.children.push(node);}};
  const doc={head,querySelector(sel){if(sel===".novegeo-feature-page")return page;if(sel.includes("future-map-viewport"))return viewport;return null;},createElement(){return {dataset:{}};}};
  const win={location:{protocol:"http:",hostname:"127.0.0.1"},addEventListener(){},removeEventListener(){},setTimeout};
  return {doc,win,page};
}

test(".15.4 experience composes from live sovereign boundary and marks styling ready",async()=>{
  const {doc,win,page}=fixture();
  const boundary={boundaryVersion:2};
  const experience=installNoveGeoCartographicStylingExperience({documentRef:doc,windowRef:win,fetchRef:()=>{},apiBaseUrl:"http://127.0.0.1:8000",createBoundaryClientRef:()=>({getActive:async()=>boundary}),mountOverlayRef:()=>({status:"RENDERED",disconnect(){}})});
  const result=await experience.refresh();
  assert.equal(result.status,"RENDERED");
  assert.equal(page.dataset.cartographicStyling,"READY");
  assert.equal(doc.head.children.length,1);
  experience.disconnect();
});
