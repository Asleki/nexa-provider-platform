import test from "node:test";
import assert from "node:assert/strict";
import { resolveCoordinateSearch, viewportPointToCoordinate } from "../../../src/map/selection/coordinate-search.js";
import { coordinateToViewportPoint } from "../../../src/map/selection/location-selection.js";

const extent = { minLongitude: 29, minLatitude: -8, maxLongitude: 45, maxLatitude: 8 };
const nav = { zoom: 2, offsetX: 30, offsetY: -20 };
const padding = 32;

test("P006.3 coordinate search creates a reference, never a registry identity", () => {
  const result = resolveCoordinateSearch({ longitude: 35.5, latitude: -1.25, extent });
  assert.equal(result.coordinateReferenceId, "crs:novegeo:geographic");
  assert.equal(result.registryAuthorityCreated, false);
  assert.match(result.selectionReferenceId, /^selection:novegeo:coordinate:/);
  assert.throws(() => resolveCoordinateSearch({ longitude: 80, latitude: 0, extent }), /outside the governed NoveGeo map extent/);
});

test("P006.3 viewport selection round-trips through current pan and zoom state", () => {
  const selected = resolveCoordinateSearch({ longitude: 36, latitude: 2, extent });
  const point = coordinateToViewportPoint({ coordinate: selected.selectedCoordinate, extent, viewportWidth: 640, viewportHeight: 435, padding, navigationState: nav });
  const roundTrip = viewportPointToCoordinate({ x: point.x, y: point.y, viewportWidth: 640, viewportHeight: 435, padding, extent, navigationState: nav });
  assert.ok(Math.abs(roundTrip.selectedCoordinate.longitude - 36) < 1e-9);
  assert.ok(Math.abs(roundTrip.selectedCoordinate.latitude - 2) < 1e-9);
});


test("P006.3 map taps outside the governed drawable extent are rejected", () => {
  assert.throws(() => viewportPointToCoordinate({ x: 2, y: 2, viewportWidth: 640, viewportHeight: 435, padding, extent, navigationState: { zoom: 1, offsetX: 0, offsetY: 0 } }), /outside the governed geographic drawing extent/);
});
