import test from "node:test";
import assert from "node:assert/strict";
import { MAP_LAYER_ORDER, MapFitMode, freezeExtent } from "../../../src/map/presentation/contracts.js";

test("map presentation contracts preserve distinct layer order and fit modes", () => {
  assert.deepEqual(MAP_LAYER_ORDER, ["background", "graticule", "equator", "boundary_fill", "boundary_stroke", "labels", "diagnostics"]);
  assert.equal(MapFitMode.BOUNDARY, "boundary");
  assert.equal(Object.isFrozen(MAP_LAYER_ORDER), true);
});

test("map extents are finite, ordered and bounded by the locked geographic CRS", () => {
  assert.deepEqual(freezeExtent({ minLongitude: 29, minLatitude: -8, maxLongitude: 45, maxLatitude: 8 }), {
    minLongitude: 29, minLatitude: -8, maxLongitude: 45, maxLatitude: 8,
  });
  assert.throws(() => freezeExtent({ minLongitude: 50, minLatitude: -8, maxLongitude: 45, maxLatitude: 8 }), /minimums/);
  assert.throws(() => freezeExtent({ minLongitude: -181, minLatitude: -8, maxLongitude: 45, maxLatitude: 8 }), /exceeds/);
});
