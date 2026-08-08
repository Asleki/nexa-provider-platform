import test from "node:test";
import assert from "node:assert/strict";
import { calculateEquatorLabelY } from "../../../src/map/interaction/map-navigation-discovery.js";

const extent = { minLongitude: 29, minLatitude: -8, maxLongitude: 45, maxLatitude: 8 };
test("Bundle 12A keeps Equator · 0° label inside the visible map frame during navigation", () => {
  const height = 400;
  assert.equal(calculateEquatorLabelY({ extent, height, navigationState: { zoom: 1, offsetY: 0 } }), 200);
  assert.equal(calculateEquatorLabelY({ extent, height, navigationState: { zoom: 8, offsetY: 9999 } }), 380);
  assert.equal(calculateEquatorLabelY({ extent, height, navigationState: { zoom: 8, offsetY: -9999 } }), 14);
});
