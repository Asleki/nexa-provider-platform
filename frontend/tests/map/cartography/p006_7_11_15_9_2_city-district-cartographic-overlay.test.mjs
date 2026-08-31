import test from "node:test";
import assert from "node:assert/strict";
import { normalizeCityDistrictPolygons } from "../../../src/map/cartography/city-district-cartographic-overlay.js";

test("CITY_DISTRICT overlay accepts governed polygonal GeoJSON only", () => {
  const polygon = { type: "Polygon", coordinates: [[]] };
  const multi = { type: "MultiPolygon", coordinates: [[[]], [[]]] };
  assert.equal(normalizeCityDistrictPolygons(polygon).length, 1);
  assert.equal(normalizeCityDistrictPolygons(multi).length, 2);
  assert.throws(() => normalizeCityDistrictPolygons({ type: "Point", coordinates: [0, 0] }));
});
