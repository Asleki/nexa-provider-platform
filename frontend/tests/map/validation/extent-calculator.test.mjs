import test from "node:test";
import assert from "node:assert/strict";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";
import { deriveBoundaryExtent } from "../../../src/map/validation/extent-calculator.js";

test("boundary extent is derived from every governed position", () => {
  const result = deriveBoundaryExtent(BUNDLED_WORLD_BOUNDARY_PUBLICATION.geometry);
  assert.deepEqual(result.extent, BUNDLED_WORLD_BOUNDARY_PUBLICATION.extent);
  assert.equal(result.positionCount, 8);
});
