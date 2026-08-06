import test from "node:test";
import assert from "node:assert/strict";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";
import { createViewport } from "../../../src/map/presentation/viewport.js";
import { qualifyMapCore } from "../../../src/map/validation/qualification.js";
import { renderMapCanvas } from "../../../src/map/presentation/canvas-renderer.js";

function fakeCanvas() {
  const context = new Proxy({ setTransform(){}, clearRect(){}, fillRect(){}, save(){}, restore(){}, beginPath(){}, moveTo(){}, lineTo(){}, stroke(){}, closePath(){}, fill(){}, setLineDash(){}, fillText(){} }, { set(t,k,v){t[k]=v;return true;} });
  return { style: {}, getContext: () => context };
}

test("P004.1 through P004.5 complete one qualified render pipeline", () => {
  const viewport = createViewport({ cssWidth: 640, cssHeight: 435, extent: BUNDLED_WORLD_BOUNDARY_PUBLICATION.extent });
  const qualification = qualifyMapCore({ publication: BUNDLED_WORLD_BOUNDARY_PUBLICATION, viewport });
  const render = renderMapCanvas({ canvas: fakeCanvas(), viewport, boundaryPlan: qualification.renderPlan, grid: qualification.grid });
  assert.equal(qualification.status, "PASSED");
  assert.equal(render.status, "RENDERED");
  assert.equal(render.boundaryId, BUNDLED_WORLD_BOUNDARY_PUBLICATION.boundaryId);
});
