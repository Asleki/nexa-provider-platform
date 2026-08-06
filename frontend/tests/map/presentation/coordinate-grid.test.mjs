import test from "node:test";
import assert from "node:assert/strict";
import { createViewport } from "../../../src/map/presentation/viewport.js";
import { createCoordinateGrid } from "../../../src/map/presentation/coordinate-grid.js";

test("coordinate grid derives longitude, latitude and a distinct equator", () => {
  const viewport = createViewport({ cssWidth: 600, cssHeight: 400, extent: { minLongitude: 29, minLatitude: -8, maxLongitude: 45, maxLatitude: 8 } });
  const grid = createCoordinateGrid(viewport, { longitudeInterval: 5, latitudeInterval: 5 });
  assert.deepEqual(grid.longitudeLines.map((line) => line.value), [30, 35, 40, 45]);
  assert.deepEqual(grid.latitudeLines.map((line) => line.value), [-5, 5]);
  assert.equal(grid.equator.value, 0);
  assert.equal(grid.equator.label, "Equator · 0°");
});
