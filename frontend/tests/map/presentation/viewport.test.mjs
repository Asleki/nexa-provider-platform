import test from "node:test";
import assert from "node:assert/strict";
import { createViewport, geographicToViewport } from "../../../src/map/presentation/viewport.js";

test("viewport separates CSS dimensions from high-density render dimensions", () => {
  const viewport = createViewport({ cssWidth: 600, cssHeight: 400, devicePixelRatio: 2, padding: 20, extent: { minLongitude: 29, minLatitude: -8, maxLongitude: 45, maxLatitude: 8 } });
  assert.equal(viewport.renderWidth, 1200);
  assert.equal(viewport.renderHeight, 800);
  assert.equal(viewport.drawableWidth, 560);
  assert.equal(viewport.drawableHeight, 360);
});

test("extent corners deterministically map to viewport padding edges", () => {
  const viewport = createViewport({ cssWidth: 600, cssHeight: 400, padding: 20, extent: { minLongitude: 29, minLatitude: -8, maxLongitude: 45, maxLatitude: 8 } });
  assert.deepEqual({ ...geographicToViewport(29, 8, viewport), viewportId: undefined, viewportVersion: undefined }, { x: 20, y: 20, viewportId: undefined, viewportVersion: undefined });
  const lowerRight = geographicToViewport(45, -8, viewport);
  assert.ok(Math.abs(lowerRight.x - 580) < 1e-9);
  assert.ok(Math.abs(lowerRight.y - 380) < 1e-9);
});
