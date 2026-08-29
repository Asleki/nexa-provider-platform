import test from "node:test";
import assert from "node:assert/strict";
import { mountNoveGeoRegionCartographicOverlay } from "../../../src/map/cartography/region-cartographic-overlay.js";
import { OFFICIAL_NOVEGEO_REGION_IDS } from "../../../src/map/cartography/region-anchor.js";

function context2d(){
  return {
    paths:0,strokes:0,fills:0,text:[],
    setTransform(){},clearRect(){},save(){},restore(){},beginPath(){this.paths+=1;},
    moveTo(){},lineTo(){},closePath(){},fill(){this.fills+=1;},stroke(){this.strokes+=1;},
    measureText(value){return {width:String(value).length*0.1};},
    strokeText(value){this.text.push(String(value));},fillText(){},
  };
}

function fixture(){
  const ctx=context2d();
  const base={style:{transform:"translate(0px, 0px) scale(1.2)"}};
  const children=[];
  const container={
    dataset:{mapZoom:"1.2"},style:{},clientWidth:640,
    getBoundingClientRect(){return {width:640};},
    querySelector(selector){
      if(selector==="[data-role='novegeo-map-canvas']")return base;
      const role=selector.match(/data-role='([^']+)'/)?.[1];
      return children.find(x=>x.role===role)||null;
    },
    appendChild(node){children.push(node);node.parent=container;},
  };
  const documentRef={
    querySelector(selector){if(selector==="[data-role='future-map-viewport']")return container;return null;},
    createElement(){return {style:{},setAttribute(name,value){if(name==="data-role")this.role=value;},getContext(){return ctx;},remove(){const i=children.indexOf(this);if(i>=0)children.splice(i,1);}};},
  };
  return {documentRef,container,ctx};
}

function polygon(x,y){return {type:"Polygon",coordinates:[[[x,y],[x+1,y],[x+1,y+1],[x,y+1],[x,y]]]};}
function multi(x,y){return {type:"MultiPolygon",coordinates:[polygon(x,y).coordinates,polygon(x+1.3,y).coordinates]};}
function region(id,index){
  const x=29.4+(index%4)*3.5;
  const y=-6.5+Math.floor(index/4)*7;
  const geometry=index>=6?multi(x,y):polygon(x,y);
  return {
    subjectId:id,family:"ADMINISTRATIVE_AREA",displayName:`Region ${index+1}`,
    publicationReference:`publication:nngla:region:${index+1}`,publicEligible:true,mapRenderable:true,
    geometryId:`NG-GEO-${String(100001+index).padStart(6,"0")}`,geometryVersion:1,
    geometryType:geometry.type==="Polygon"?"POLYGON":"MULTIPOLYGON",crsCode:"NG-CRS-EPSG4326",geometry,
    runtimeEffectScope:"SHARED_REFERENCE",classificationScheme:"NNGLA_ADMIN_TYPE",classificationCode:"REGION",
    labelPoint:{type:"Point",coordinates:[x+0.5,y+0.5]},labelAnchorKind:"DERIVED_PRESENTATION",
    labelPointAlgorithmId:"algorithm:nngla:region-label-point-on-surface:epsg4326",labelPointAlgorithmVersion:1,
  };
}

test("REGION overlay renders 6 Polygon + 2 MultiPolygon and eight zoom-eligible labels",()=>{
  const {documentRef,container,ctx}=fixture();
  const items=OFFICIAL_NOVEGEO_REGION_IDS.map(region);
  const boundary={extent:{minLongitude:29,minLatitude:-8,maxLongitude:45,maxLatitude:8}};
  const overlay=mountNoveGeoRegionCartographicOverlay(documentRef,{boundaryPublication:boundary,regionItems:items,readRuntime:"simulation",observeResize:false,observeNavigation:false,devicePixelRatio:1});
  assert.equal(overlay.status,"RENDERED");
  assert.equal(overlay.firstReceipt.regionCount,8);
  assert.equal(overlay.firstReceipt.polygonPartCount,10);
  assert.equal(overlay.firstReceipt.labelCandidateCount,8);
  assert.equal(overlay.firstReceipt.labelPlanCount,8);
  assert.equal(overlay.firstReceipt.labelRenderedCount,8);
  assert.deepEqual(overlay.firstReceipt.renderedRegionIds,[...OFFICIAL_NOVEGEO_REGION_IDS]);
  assert.equal(container.dataset.novegeoRegionCount,"8");
  assert.equal(container.dataset.novegeoRegionLabelCount,"8");
  assert.equal(ctx.paths,8);
  overlay.disconnect();
  assert.equal(container.dataset.novegeoRegionCount,undefined);
});

test("locked ADMIN_REGION zoom threshold remains respected at zoom 1",()=>{
  const {documentRef,container}=fixture();
  container.dataset.mapZoom="1";
  const base=container.querySelector("[data-role='novegeo-map-canvas']");
  base.style.transform="translate(0px, 0px) scale(1)";
  const items=OFFICIAL_NOVEGEO_REGION_IDS.map(region);
  const overlay=mountNoveGeoRegionCartographicOverlay(documentRef,{boundaryPublication:{extent:{minLongitude:29,minLatitude:-8,maxLongitude:45,maxLatitude:8}},regionItems:items,readRuntime:"simulation",observeResize:false,observeNavigation:false,devicePixelRatio:1});
  assert.equal(overlay.firstReceipt.regionCount,8);
  assert.equal(overlay.firstReceipt.labelCandidateCount,8);
  assert.equal(overlay.firstReceipt.labelPlanCount,0);
  assert.equal(overlay.firstReceipt.labelRenderedCount,0);
});
