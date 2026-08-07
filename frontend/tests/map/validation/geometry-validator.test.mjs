import test from "node:test";
import assert from "node:assert/strict";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";
import { validateBoundaryGeometry } from "../../../src/map/validation/geometry-validator.js";

function countRings(geometry) {
  return geometry.coordinates.reduce((total, polygon) => total + polygon.length, 0);
}

function countPositions(geometry) {
  return geometry.coordinates.reduce(
    (polygons, polygon) => polygons + polygon.reduce((rings, ring) => rings + ring.length, 0),
    0,
  );
}

test("governed MultiPolygon rings and positions validate deeply", () => {
  const result = validateBoundaryGeometry(BUNDLED_WORLD_BOUNDARY_PUBLICATION.geometry);
  assert.equal(result.polygonCount, BUNDLED_WORLD_BOUNDARY_PUBLICATION.geometry.coordinates.length);
  assert.equal(result.polygonCount, 6);
  assert.equal(result.ringCount, countRings(BUNDLED_WORLD_BOUNDARY_PUBLICATION.geometry));
  assert.equal(result.positionCount, countPositions(BUNDLED_WORLD_BOUNDARY_PUBLICATION.geometry));
});

test("open and duplicate rings are rejected", () => {
  assert.throws(() => validateBoundaryGeometry({ type: "MultiPolygon", coordinates: [[[[0,0],[1,0],[1,1],[0,1]]]] }), /closed/);
  assert.throws(() => validateBoundaryGeometry({ type: "MultiPolygon", coordinates: [[[[0,0],[1,0],[1,0],[0,0]]]] }), /consecutive duplicate/);
});
