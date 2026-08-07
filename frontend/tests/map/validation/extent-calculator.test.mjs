import test from "node:test";
import assert from "node:assert/strict";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";
import { deriveBoundaryExtent } from "../../../src/map/validation/extent-calculator.js";

function countPositions(geometry) {
  return geometry.coordinates.reduce(
    (polygons, polygon) => polygons + polygon.reduce(
      (rings, ring) => rings + ring.length,
      0,
    ),
    0,
  );
}

test("boundary extent is derived from every governed position", () => {
  const result = deriveBoundaryExtent(BUNDLED_WORLD_BOUNDARY_PUBLICATION.geometry);
  assert.deepEqual(result.extent, BUNDLED_WORLD_BOUNDARY_PUBLICATION.extent);
  assert.equal(result.positionCount, countPositions(BUNDLED_WORLD_BOUNDARY_PUBLICATION.geometry));
  assert.ok(result.positionCount > BUNDLED_WORLD_BOUNDARY_PUBLICATION.derivativeVertexCount);
});
