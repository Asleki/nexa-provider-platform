import test from "node:test";
import assert from "node:assert/strict";
import { createScaleModel } from "../../../src/map/controls/scale.js";

const extent = { minLongitude: 29, maxLongitude: 45 };
test("P006.2 scale responds deterministically to zoom rather than remaining fake/static", () => {
  const base = createScaleModel({ extent, zoom: 1, viewportWidth: 500 });
  const zoomed = createScaleModel({ extent, zoom: 4, viewportWidth: 500 });
  assert.ok(zoomed.visibleLongitudeDegrees < base.visibleLongitudeDegrees);
  assert.ok(zoomed.distanceKm <= base.distanceKm);
  assert.equal(base.approximation, "geographic_equatorial_reference");
});
