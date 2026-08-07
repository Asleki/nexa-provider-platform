import test from "node:test";
import assert from "node:assert/strict";
import { mountPhysicalLandPresentation } from "../../../src/map/environment/physical-land-presentation.js";

function context() {
  const alphaWrites=[];
  return {
    alphaWrites,
    _globalAlpha:1,
    setTransform(){},clearRect(){},save(){},restore(){},beginPath(){},moveTo(){},lineTo(){},closePath(){},clip(){},fillRect(){},arc(){},fill(){},
    set fillStyle(value){ this._fillStyle=value; }, get fillStyle(){ return this._fillStyle; },
    set globalAlpha(value){ this._globalAlpha=value; alphaWrites.push(value); }, get globalAlpha(){ return this._globalAlpha; },
  };
}
function canvas(role="") {
  const attrs={}; const ctx=context();
  return { style:{}, width:0,height:0,setAttribute(k,v){attrs[k]=v;},getAttribute(k){return attrs[k];},getContext(){return ctx;},ctx,role };
}

test("P005.1/P005.2 physical land composites above locked P004 with reference-safe transparency", () => {
  const boundary=canvas("boundary");
  const children=[boundary];
  const container={style:{},clientWidth:420,getBoundingClientRect(){return {width:420};},querySelector(selector){
    if(selector==="[data-role='novegeo-map-canvas']") return boundary;
    if(selector==="[data-role='novegeo-physical-land-canvas']") return children.find((node)=>node.getAttribute?.("data-role")==="novegeo-physical-land-canvas") || null;
    return null;
  },insertBefore(node,before){children.splice(children.indexOf(before),0,node);}};
  const documentRef={querySelector(){return container;},createElement(){return canvas("terrain");}};
  const receipt=mountPhysicalLandPresentation(documentRef,{devicePixelRatio:1});
  assert.equal(receipt.status,"RENDERED");
  assert.equal(receipt.terrainDatasetVersion,1);
  assert.ok(receipt.terrainSampleCount>1000);
  assert.ok(receipt.landformFeatureCount>=8);
  assert.equal(children.length,2);
  assert.equal(children[0].style.zIndex,"2");
  assert.equal(boundary.style.zIndex,"1");
  assert.equal(children[0].style.pointerEvents,"none");
  assert.ok(children[0].ctx.alphaWrites.some((value)=>value>0 && value<1));
});

test("P005 physical-land remount repaints the existing canvas without duplication", () => {
  const boundary=canvas("boundary");
  const physical=canvas("terrain");
  physical.setAttribute("data-role","novegeo-physical-land-canvas");
  const children=[physical,boundary];
  const container={
    style:{},clientWidth:420,getBoundingClientRect(){return {width:420};},
    querySelector(selector){
      if(selector==="[data-role='novegeo-map-canvas']") return boundary;
      if(selector==="[data-role='novegeo-physical-land-canvas']") return physical;
      return null;
    },
    insertBefore(node,before){children.splice(children.indexOf(before),0,node);},
  };
  const documentRef={querySelector(){return container;},createElement(){throw new Error("must reuse existing canvas");}};
  const receipt=mountPhysicalLandPresentation(documentRef,{devicePixelRatio:1});
  assert.equal(receipt.status,"RENDERED");
  assert.equal(children.length,2);
  assert.equal(children[0],physical);
});
