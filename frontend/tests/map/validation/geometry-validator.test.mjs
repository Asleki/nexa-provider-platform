import test from "node:test";
import assert from "node:assert/strict";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";
import { validateBoundaryGeometry } from "../../../src/map/validation/geometry-validator.js";

test("governed MultiPolygon rings and positions validate deeply", () => {
  const result = validateBoundaryGeometry(BUNDLED_WORLD_BOUNDARY_PUBLICATION.geometry);
  assert.equal(result.polygonCount, 1);
  assert.equal(result.ringCount, 1);
  assert.equal(result.positionCount, 8);
});

test("open and duplicate rings are rejected", () => {
  assert.throws(() => validateBoundaryGeometry({ type: "MultiPolygon", coordinates: [[[[0,0],[1,0],[1,1],[0,1]]]] }), /closed/);
  assert.throws(() => validateBoundaryGeometry({ type: "MultiPolygon", coordinates: [[[[0,0],[1,0],[1,0],[0,0]]]] }), /consecutive duplicate/);
});
