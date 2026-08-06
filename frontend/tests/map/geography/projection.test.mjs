import assert from "node:assert/strict";
import test from "node:test";

import { projectCoordinate, unprojectCoordinate } from "../../../src/map/geography/projection.js";

test("P004 projection maps and restores coordinates deterministically", () => {
  const projected = projectCoordinate(34.25, -1.5);
  const restored = unprojectCoordinate(projected);
  assert.ok(Math.abs(restored.longitude - 34.25) <= 1e-8);
  assert.ok(Math.abs(restored.latitude + 1.5) <= 1e-8);
});

test("P004 projection maps world extremes to normalized coordinates", () => {
  assert.deepEqual(projectCoordinate(-180, 90), {
    x: 0,
    y: 0,
    projectionId: "projection:novegeo:equirectangular-world",
    projectionVersion: 1,
  });
  assert.equal(projectCoordinate(180, -90).x, 1);
  assert.equal(projectCoordinate(180, -90).y, 1);
});
