import assert from "node:assert/strict";
import test from "node:test";

import { COORDINATE_REFERENCE, createGeographicCoordinate, validateWorldBoundaryPublication } from "../../../src/map/geography/contracts.js";

test("P004 coordinate contract uses explicit longitude latitude order", () => {
  assert.deepEqual(COORDINATE_REFERENCE.axisOrder, ["longitude", "latitude"]);
  assert.deepEqual(createGeographicCoordinate(0, 0), { longitude: 0, latitude: 0 });
  assert.throws(() => createGeographicCoordinate(181, 0), /longitude/);
});

test("P004 browser accepts only the typed MultiPolygon publication", () => {
  const value = {
    boundaryId: "boundary:novegeo:sovereign",
    boundaryVersion: 1,
    geometry: { type: "MultiPolygon", coordinates: [] },
    coordinateReference: { ...COORDINATE_REFERENCE, axisOrder: [...COORDINATE_REFERENCE.axisOrder] },
  };
  assert.equal(validateWorldBoundaryPublication(value).boundaryVersion, 1);
  assert.throws(() => validateWorldBoundaryPublication({ ...value, geometry: { type: "Point" } }), /MultiPolygon/);
});
