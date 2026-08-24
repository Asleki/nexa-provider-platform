import test from "node:test";
import assert from "node:assert/strict";
import {mountNoveGeoCartographicOverlay} from "../../../src/map/cartography/cartographic-overlay.js";

const boundary={boundaryId:"boundary:novegeo:sovereign",boundaryVersion:2,publicationId:"publication:novegeo:world-boundary:v2",coordinateReference:{coordinateReferenceId:"crs:novegeo:geographic",version:1,axisOrder:["longitude","latitude"]},extent:{minLongitude:0,minLatitude:0,maxLongitude:10,maxLatitude:10},geometry:{type:"MultiPolygon",coordinates:[[[[0,0],[10,0],[10,10],[0,10],[0,0]]]]}};
function makeContext(){return {save(){},restore(){},setTransform(){},clearRect(){},measureText(t){return {width:t.length*7};},strokeText(){},fillText(){}};}
function fixture(){
  const base={style:{transform:"translate(0px, 0px) scale(1)",transformOrigin:"50% 50%",willChange:"transform"}};
  const nodes={"novegeo-map-canvas":base};
  const container={dataset:{mapZoom:"1"},style:{},clientWidth:640,getBoundingClientRect(){return {width:640};},querySelector(selector){const m=selector.match(/data-role='([^']+)'|data-role="([^"]+)"/);return m?nodes[m[1]||m[2]]||null:null;},appendChild(node){nodes[node.role]=node;node.parentNode=this;}};
  const doc={querySelector(sel){return sel.includes("future-map-viewport")?container:null;},createElement(){return {style:{},setAttribute(name,value){if(name==="data-role")this.role=value;},getContext(){return makeContext();},remove(){delete nodes[this.role];}};}};
  return {doc,container,nodes};
}

test(".15.4 mounts one additive cartographic overlay without replacing base map canvas",()=>{
  const {doc,container,nodes}=fixture();
  const overlay=mountNoveGeoCartographicOverlay(doc,{boundaryPublication:boundary,observeResize:false,observeNavigation:false});
  assert.equal(overlay.status,"RENDERED");
  assert.equal(container.dataset.cartographyLabelCount,"1");
  assert.ok(nodes["novegeo-map-canvas"]);
  assert.ok(nodes["novegeo-cartographic-label-canvas"]);
  overlay.disconnect();
});
