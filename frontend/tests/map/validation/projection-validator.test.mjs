import test from "node:test";
import assert from "node:assert/strict";
import { validateProjectionPositions } from "../../../src/map/validation/projection-validator.js";

test("governed positions project and restore within tolerance", () => {
  const receipt = validateProjectionPositions([[0,0],[180,90],[-180,-90]]);
  assert.equal(receipt.projectedCount, 3);
  assert.equal(receipt.projectionVersion, 1);
});
