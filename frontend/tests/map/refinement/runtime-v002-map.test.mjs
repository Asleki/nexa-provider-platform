import test from "node:test";
import assert from "node:assert/strict";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";
import { mountMapPresentation } from "../../../src/map/presentation/map-presentation.js";

function context() {
  return new Proxy({ setTransform(){}, clearRect(){}, fillRect(){}, save(){}, restore(){}, beginPath(){}, moveTo(){}, lineTo(){}, stroke(){}, closePath(){}, fill(){}, setLineDash(){}, fillText(){} }, { set(t,k,v){t[k]=v;return true;} });
}

test("runtime bridge no longer exposes historical v001 and preserves refined islands", () => {
  assert.equal(BUNDLED_WORLD_BOUNDARY_PUBLICATION.publicationId, "publication:novegeo:world-boundary:v002");
  assert.equal(BUNDLED_WORLD_BOUNDARY_PUBLICATION.boundaryVersion, 2);
  assert.equal(BUNDLED_WORLD_BOUNDARY_PUBLICATION.resolutionClass, "standard");
  assert.equal(BUNDLED_WORLD_BOUNDARY_PUBLICATION.derivativeVertexCount, 493);
  assert.equal(BUNDLED_WORLD_BOUNDARY_PUBLICATION.geometry.coordinates.length, 6);
});

test("existing P004 renderer qualifies and renders the refined v002 standard representation", () => {
  const container = { dataset:{}, clientWidth:500, querySelector(){return null;}, replaceChildren(child){this.child=child;}, getBoundingClientRect(){return {width:500,height:340};} };
  const documentRef = { querySelector(selector){return selector === "[data-role='future-map-viewport']" ? container : null;}, createElement(){return {style:{},setAttribute(){},getContext:()=>context()};} };
  const receipt = mountMapPresentation(documentRef, { observeResize:false, devicePixelRatio:1 });
  assert.equal(receipt.status, "RENDERED");
  assert.equal(receipt.boundaryVersion, 2);
  assert.equal(receipt.polygonCount, 6);
  assert.equal(receipt.qualificationStatus, "PASSED");
});
