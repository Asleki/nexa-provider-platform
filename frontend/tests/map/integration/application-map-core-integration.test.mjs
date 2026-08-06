import test from "node:test";
import assert from "node:assert/strict";
import { mountMapPresentation } from "../../../src/map/presentation/map-presentation.js";

function context() { return new Proxy({ setTransform(){}, clearRect(){}, fillRect(){}, save(){}, restore(){}, beginPath(){}, moveTo(){}, lineTo(){}, stroke(){}, closePath(){}, fill(){}, setLineDash(){}, fillText(){} }, { set(t,k,v){t[k]=v;return true;} }); }

test("application map presentation reports successful qualification and render", () => {
  const container = { dataset:{}, clientWidth:500, querySelector(){return null;}, replaceChildren(child){this.child=child;}, getBoundingClientRect(){return {width:500,height:340};} };
  const documentRef = { querySelector(selector){return selector === "[data-role='future-map-viewport']" ? container : null;}, createElement(){return {style:{},setAttribute(){},getContext:()=>context()};} };
  const receipt = mountMapPresentation(documentRef, { observeResize:false, devicePixelRatio:1 });
  assert.equal(receipt.status, "RENDERED");
  assert.equal(receipt.qualificationStatus, "PASSED");
  assert.equal(container.dataset.mapStatus, "READY");
});
