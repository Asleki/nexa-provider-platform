import test from "node:test";
import assert from "node:assert/strict";
import { validateExtentParity, assertPositionsWithinExtent } from "../../../src/map/validation/extent-validator.js";

test("declared and derived extents must match", () => {
  const extent = { minLongitude: 1, minLatitude: 2, maxLongitude: 3, maxLatitude: 4 };
  assert.equal(validateExtentParity(extent, extent).matched, true);
  assert.throws(() => validateExtentParity(extent, { ...extent, maxLongitude: 3.5 }), /does not match/);
});

test("all positions must remain inside the declared extent", () => {
  const extent = { minLongitude: 0, minLatitude: 0, maxLongitude: 10, maxLatitude: 10 };
  assert.doesNotThrow(() => assertPositionsWithinExtent([[0,0],[10,10]], extent));
  assert.throws(() => assertPositionsWithinExtent([[11,5]], extent), /outside/);
});
