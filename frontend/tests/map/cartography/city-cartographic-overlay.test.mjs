import test from "node:test";
import assert from "node:assert/strict";
import { mountNoveGeoCityCartographicOverlay } from "../../../src/map/cartography/city-cartographic-overlay.js";

function context2d(){
  return {
    paths:0,strokes:0,fills:0,text:[],
    setTransform(){},clearRect(){},save(){},restore(){},beginPath(){this.paths+=1;},
    moveTo(){},lineTo(){},closePath(){},fill(){this.fills+=1;},stroke(){this.strokes+=1;},
    measureText(value){return {width:String(value).length*0.1};},
    strokeText(value){this.text.push(String(value));},fillText(){},
  };
}
function fixture(zoom="2"){
  const ctx=context2d();
  const base={style:{transform:`translate(0px, 0px) scale(${zoom})`}};
  const children=[];
  const container={dataset:{mapZoom:zoom},style:{},clientWidth:640,
    getBoundingClientRect(){return {width:640};},
    querySelector(selector){if(selector==="[data-role='novegeo-map-canvas']")return base;const role=selector.match(/data-role='([^']+)'/)?.[1];return children.find(x=>x.role===role)||null;},
    appendChild(node){children.push(node);node.parent=container;},
  };
  const documentRef={querySelector(selector){if(selector==="[data-role='future-map-viewport']")return container;return null;},
    createElement(){return {style:{},setAttribute(name,value){if(name==="data-role")this.role=value;},getContext(){return ctx;},remove(){const i=children.indexOf(this);if(i>=0)children.splice(i,1);}};}};
  return {documentRef,container,ctx,children};
}
function polygon(){return {type:"Polygon",coordinates:[[[42.8,0.1],[43.3,0.1],[43.3,0.7],[42.8,0.7],[42.8,0.1]]]};}
function city(){return {subjectId:"NG-ADM-000170",family:"ADMINISTRATIVE_AREA",displayName:"Port Meridian",publicationReference:"city-publication:nngla:port-meridian",publicEligible:true,mapRenderable:true,geometryId:"city-geometry:nngla:NG-ADM-000170:v1",geometryVersion:1,geometryType:"POLYGON",crsCode:"NG-CRS-EPSG4326",geometry:polygon(),runtimeEffectScope:"SHARED_REFERENCE",classificationScheme:"NNGLA_ADMIN_TYPE",classificationCode:"CITY",parentRegionId:"NG-ADM-000008",labelPoint:{type:"Point",coordinates:[43.0,0.35]},labelPointAlgorithmId:"algorithm:nngla:city-label-point-on-surface:epsg4326",labelPointAlgorithmVersion:1};}

test("CITY overlay renders an incremental one-city pilot above REGION layer",()=>{
  const {documentRef,container,ctx,children}=fixture("2");
  const overlay=mountNoveGeoCityCartographicOverlay(documentRef,{boundaryPublication:{extent:{minLongitude:29,minLatitude:-8,maxLongitude:45,maxLatitude:8}},cityItems:[city()],readRuntime:"simulation",observeResize:false,observeNavigation:false,devicePixelRatio:1});
  assert.equal(overlay.status,"RENDERED");
  assert.equal(overlay.firstReceipt.cityCount,1);
  assert.deepEqual(overlay.firstReceipt.renderedCityIds,["NG-ADM-000170"]);
  assert.equal(overlay.firstReceipt.labelCandidateCount,1);
  assert.equal(container.dataset.novegeoCityCount,"1");
  assert.equal(children[0].style.zIndex,"4");
  assert.equal(ctx.paths,1);
  overlay.disconnect();
});

test("CITY overlay permits zero published cities without degrading map",()=>{
  const {documentRef,container}=fixture("2");
  const overlay=mountNoveGeoCityCartographicOverlay(documentRef,{boundaryPublication:{extent:{minLongitude:29,minLatitude:-8,maxLongitude:45,maxLatitude:8}},cityItems:[],readRuntime:"simulation",observeResize:false,observeNavigation:false,devicePixelRatio:1});
  assert.equal(overlay.status,"RENDERED");
  assert.equal(overlay.firstReceipt.cityCount,0);
  assert.equal(container.dataset.novegeoCityCount,"0");
});
