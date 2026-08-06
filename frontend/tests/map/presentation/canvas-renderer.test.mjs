import test from "node:test";
import assert from "node:assert/strict";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";
import { createViewport } from "../../../src/map/presentation/viewport.js";
import { createBoundaryRenderPlan } from "../../../src/map/presentation/boundary-render-plan.js";
import { createCoordinateGrid } from "../../../src/map/presentation/coordinate-grid.js";
import { renderMapCanvas } from "../../../src/map/presentation/canvas-renderer.js";

function fakeCanvas() {
  const calls = [];
  const context = new Proxy({
    setTransform: (...args) => calls.push(["setTransform", ...args]), clearRect: () => {}, fillRect: () => {}, save: () => {}, restore: () => {}, beginPath: () => {}, moveTo: () => {}, lineTo: () => {}, stroke: () => {}, closePath: () => {}, fill: (...args) => calls.push(["fill", ...args]), setLineDash: () => {}, fillText: () => {},
  }, { set(target, key, value) { target[key] = value; return true; } });
  return { width: 0, height: 0, style: {}, getContext: (kind) => kind === "2d" ? context : null, calls };
}

test("canvas adapter renders the governed boundary and equator at device density", () => {
  const viewport = createViewport({ cssWidth: 600, cssHeight: 400, devicePixelRatio: 2, extent: BUNDLED_WORLD_BOUNDARY_PUBLICATION.extent });
  const canvas = fakeCanvas();
  const receipt = renderMapCanvas({ canvas, viewport, boundaryPlan: createBoundaryRenderPlan(BUNDLED_WORLD_BOUNDARY_PUBLICATION, viewport), grid: createCoordinateGrid(viewport) });
  assert.equal(canvas.width, 1200);
  assert.equal(canvas.height, 800);
  assert.equal(receipt.status, "RENDERED");
  assert.equal(receipt.equatorRendered, true);
  assert.ok(canvas.calls.some((call) => call[0] === "fill" && call[1] === "evenodd"));
});
