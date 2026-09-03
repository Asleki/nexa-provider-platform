import test from "node:test";
import assert from "node:assert/strict";
import {
  createUniformProjectedViewport,
  geographicToUnifiedViewport,
  viewportPointToGeographic,
} from "../../../src/map/cartography/unified-projection.js";

const extent = { minLongitude: 30, minLatitude: -10, maxLongitude: 50, maxLatitude: 10 };

test("uniform projection uses one contain-fit scale without stretching", () => {
  const portrait = createUniformProjectedViewport({ cssWidth: 360, cssHeight: 760, padding: 20, extent });
  const landscape = createUniformProjectedViewport({ cssWidth: 900, cssHeight: 420, padding: 20, extent });
  const desktop = createUniformProjectedViewport({ cssWidth: 1440, cssHeight: 900, padding: 24, extent });
  assert.ok(portrait.uniformScale <= portrait.widthScale + 1e-12);
  assert.ok(portrait.uniformScale <= portrait.heightScale + 1e-12);
  assert.ok(landscape.uniformScale <= landscape.widthScale + 1e-12);
  assert.ok(landscape.uniformScale <= landscape.heightScale + 1e-12);
  assert.ok(desktop.uniformScale <= desktop.widthScale + 1e-12);
  assert.ok(desktop.uniformScale <= desktop.heightScale + 1e-12);
  assert.ok(Math.abs(portrait.fittedWidth / portrait.fittedHeight - landscape.fittedWidth / landscape.fittedHeight) < 1e-9);
  assert.ok(Math.abs(desktop.fittedWidth / desktop.fittedHeight - landscape.fittedWidth / landscape.fittedHeight) < 1e-9);
  assert.ok(Math.abs(portrait.fittedWidth / portrait.fittedHeight - 1) < 1e-9);
});

test("uniform projection round-trips through navigation", () => {
  const viewport = createUniformProjectedViewport({ cssWidth: 600, cssHeight: 500, padding: 20, extent });
  const point = geographicToUnifiedViewport(40, 0, viewport);
  const coordinate = viewportPointToGeographic(point.x, point.y, viewport, { zoom: 1, offsetX: 0, offsetY: 0 });
  assert.ok(Math.abs(coordinate.longitude - 40) < 1e-9);
  assert.ok(Math.abs(coordinate.latitude) < 1e-9);
});
