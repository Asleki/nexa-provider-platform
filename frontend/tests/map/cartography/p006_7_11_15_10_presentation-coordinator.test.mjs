import test from "node:test";
import assert from "node:assert/strict";
import { createNoveGeoPresentationCoordinator, DataState, LayoutMode, PresentationMode } from "../../../src/map/cartography/presentation-coordinator.js";

class FakeNode {
  constructor(tag = "div") { this.tagName=tag.toUpperCase();this.dataset={};this.style={};this.children=[];this.hidden=false;this.clientWidth=640;this.clientHeight=435;this.attributes={}; }
  setAttribute(name,value){this.attributes[name]=String(value);if(name==="data-role")this.dataset.role=String(value);}
  append(...nodes){for(const node of nodes)this.appendChild(node);}
  appendChild(node){this.children.push(node);node.parentNode=this;return node;}
  querySelector(selector){if(selector==="[data-role='novegeo-map-canvas']")return this.children.find((n)=>n.dataset.role==="novegeo-map-canvas")||null;const match=selector.match(/^\[data-role='([^']+)'\]$/);if(match)return this.children.find((n)=>n.dataset.role===match[1])||null;return null;}
  querySelectorAll(selector){if(selector==="canvas[data-role]")return this.children.filter((n)=>n.tagName==="CANVAS"&&n.dataset.role);return [];}
  getBoundingClientRect(){return {width:this.clientWidth,height:this.clientHeight};}
}
function fixture(renderFrameRef){
  const root=new FakeNode("div"),page=new FakeNode("section"),viewport=new FakeNode("div"),base=new FakeNode("canvas");
  base.setAttribute("data-role","novegeo-map-canvas");base.style.transform="translate(0px, 0px) scale(1)";viewport.appendChild(base);
  page.querySelector=(selector)=>selector==="[data-role='future-map-viewport']"?viewport:null;
  const head=new FakeNode("head");
  const listeners=new Map();
  const on=(type,handler)=>{if(!listeners.has(type))listeners.set(type,new Set());listeners.get(type).add(handler);};
  const off=(type,handler)=>listeners.get(type)?.delete(handler);
  const documentRef={head,createElement:(tag)=>new FakeNode(tag),querySelector(selector){if(selector===".novegeo-feature-page")return page;if(selector==="[data-role='future-map-viewport']")return viewport;if(selector==="#nexilabs-app")return root;if(selector==="link[data-novegeo-map-first-style='true']")return null;return null;},addEventListener:on,removeEventListener:off};
  const windowRef={devicePixelRatio:1,innerWidth:640,innerHeight:435,addEventListener(){},removeEventListener(){}};
  const coordinator=createNoveGeoPresentationCoordinator({documentRef,windowRef,renderFrameRef});
  coordinator.attachViewport({documentRef,windowRef});
  const dispatchChange=(target)=>{for(const handler of listeners.get("change")||[])handler({target});};
  return {coordinator,base,viewport,page,root,documentRef,windowRef,dispatchChange};
}
const boundary={boundaryId:"boundary:novegeo:test",boundaryVersion:1,publicationId:"publication:novegeo:test",coordinateReference:{coordinateReferenceId:"crs:novegeo:geographic",version:1,axisOrder:["longitude","latitude"]},extent:{minLongitude:30,minLatitude:-10,maxLongitude:50,maxLatitude:10},geometry:{type:"MultiPolygon",coordinates:[[[[30,-10],[50,-10],[50,10],[30,10],[30,-10]]]]}};
const keys=["REGION","CITY","MUNICIPALITY","CITY_DISTRICT","TOWN"];
const frame={status:"RENDERED",semanticBand:"NATIONAL",scale:{widthPx:80,metricLabel:"100 km",imperialLabel:"62 mi"},visibleSubjectIds:[],collisionRejectedSubjectIds:[],sourceCandidateCount:1,publicationEligibleCount:1,zoomEligibleCount:1,collisionAcceptedCount:1,collisionRejectedCount:0,geographicCenter:{longitude:37,latitude:0}};

test("coordinator enters MAP_FIRST immediately and activates UNIFIED from boundary without waiting for optional snapshots",()=>{
  const {coordinator,base,viewport,page,root}=fixture(()=>frame);
  assert.equal(coordinator.layoutMode,LayoutMode.MAP_FIRST);
  assert.equal(coordinator.mode,PresentationMode.LEGACY);
  assert.equal(coordinator.dataState,DataState.LOADING);
  assert.equal(page.dataset.novegeoLayoutMode,"MAP_FIRST");
  assert.equal(root.dataset.novegeoLayoutMode,"MAP_FIRST");
  coordinator.bindBoundary(boundary);
  assert.equal(coordinator.mode,PresentationMode.UNIFIED);
  assert.equal(base.style.visibility,"hidden");
  assert.equal(viewport.querySelector("[data-role='novegeo-unified-cartographic-canvas']").style.visibility,"visible");
  assert.equal(coordinator.latestReceipt.activePresentationMode,"UNIFIED");
  assert.equal(coordinator.latestReceipt.authorityBoundary.boundaryId,boundary.boundaryId);
  assert.equal(Object.keys(coordinator.latestReceipt.snapshotSources).length,0);
});

test("failed unified frame keeps MAP_FIRST layout while retaining the working legacy renderer",()=>{
  const {coordinator,base,page}=fixture(()=>{throw new Error("synthetic_render_failure");});
  coordinator.bindBoundary(boundary);
  assert.equal(coordinator.mode,PresentationMode.LEGACY);
  assert.equal(coordinator.layoutMode,LayoutMode.MAP_FIRST);
  assert.equal(page.dataset.novegeoLayoutMode,"MAP_FIRST");
  assert.notEqual(base.style.visibility,"hidden");
  assert.match(coordinator.latestReceipt.reason,/synthetic_render_failure/);
});

test("optional governed snapshots redraw progressively and data state reaches READY only after all five",()=>{
  let renders=0;const {coordinator}=fixture(()=>{renders+=1;return frame;});
  coordinator.bindBoundary(boundary);assert.equal(renders,1);
  coordinator.registerLayerSnapshot({layerKey:"REGION",items:[],candidates:[]});
  assert.equal(coordinator.dataState,DataState.PARTIAL);assert.equal(renders,2);
  for(const key of keys.slice(1))coordinator.registerLayerSnapshot({layerKey:key,items:[],candidates:[]});
  assert.equal(coordinator.dataState,DataState.READY);assert.equal(renders,6);
  assert.equal(Object.keys(coordinator.latestReceipt.snapshotSources).length,5);
});

test("a degraded optional layer changes dataState only and never revokes MAP_FIRST or UNIFIED ownership",()=>{
  const {coordinator}=fixture(()=>frame);coordinator.bindBoundary(boundary);
  const receipt=coordinator.markLayerDegraded("TOWN","synthetic_timeout");
  assert.equal(receipt.status,"LAYER_DEGRADED");
  assert.equal(coordinator.dataState,DataState.DEGRADED);
  assert.equal(coordinator.layoutMode,LayoutMode.MAP_FIRST);
  assert.equal(coordinator.mode,PresentationMode.UNIFIED);
  coordinator.registerLayerSnapshot({layerKey:"TOWN",items:[],candidates:[]});
  assert.equal(coordinator.dataState,DataState.PARTIAL);
});

test("country label remains exact NoveGeo casing in the boundary-only base frame",()=>{
  let seen=null;
  const {coordinator}=fixture((input)=>{seen=input.countryCandidate;return frame;});
  coordinator.bindBoundary(boundary);
  assert.equal(seen.displayName,"NoveGeo");
  assert.notEqual(seen.displayName,"NOVEGEO");
});

test("all four historical environmental controls are enabled in the first unified frame",()=>{
  let seen=null;
  const {coordinator}=fixture((input)=>{seen=input;return frame;});
  coordinator.bindBoundary(boundary);
  assert.deepEqual({...seen.environmentalLayerVisibility},{physicalLand:true,biosphere:true,hydrologyAtmosphere:true,coordinates:true});
  assert.equal(seen.userLayerVisibility.REFERENCE,true);
});

test("physical land, biosphere and water-atmosphere controls redraw unified environment truthfully",()=>{
  const seen=[];
  const {coordinator,dispatchChange}=fixture((input)=>{seen.push({env:{...input.environmentalLayerVisibility},ref:input.userLayerVisibility.REFERENCE});return frame;});
  coordinator.bindBoundary(boundary);
  for(const key of ["physicalLand","biosphere","hydrologyAtmosphere"]){
    dispatchChange({dataset:{layerKey:key},checked:false});
    assert.equal(seen.at(-1).env[key],false,key);
  }
  assert.equal(coordinator.mode,PresentationMode.UNIFIED);
});

test("coordinates control couples unified graticule visibility and REFERENCE label visibility",()=>{
  const seen=[];
  const {coordinator,dispatchChange}=fixture((input)=>{seen.push({env:{...input.environmentalLayerVisibility},ref:{...input.userLayerVisibility}});return frame;});
  coordinator.bindBoundary(boundary);
  dispatchChange({dataset:{layerKey:"coordinates"},checked:false});
  assert.equal(seen.at(-1).env.coordinates,false);
  assert.equal(seen.at(-1).ref.REFERENCE,false);
  dispatchChange({dataset:{layerKey:"coordinates"},checked:true});
  assert.equal(seen.at(-1).env.coordinates,true);
  assert.equal(seen.at(-1).ref.REFERENCE,true);
});

test("environment visibility resets only across presentation generations and remains re-applicable by restored layer events",()=>{
  const seen=[];
  const first=fixture((input)=>{seen.push({...input.environmentalLayerVisibility});return frame;});
  first.coordinator.bindBoundary(boundary);
  first.dispatchChange({dataset:{layerKey:"physicalLand"},checked:false});
  assert.equal(seen.at(-1).physicalLand,false);
  first.coordinator.disconnect();
  first.coordinator.attachViewport({documentRef:first.documentRef,windowRef:first.windowRef});
  first.coordinator.bindBoundary(boundary);
  assert.equal(seen.at(-1).physicalLand,true);
  first.dispatchChange({dataset:{layerKey:"physicalLand"},checked:false});
  assert.equal(seen.at(-1).physicalLand,false);
});
