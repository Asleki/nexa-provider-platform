import test from "node:test";
import assert from "node:assert/strict";
import { normalizeTownPolygons } from "../../../src/map/cartography/town-cartographic-overlay.js";

test("TOWN overlay accepts governed polygonal GeoJSON only", () => {
  const polygon = { type: "Polygon", coordinates: [[]] };
  const multi = { type: "MultiPolygon", coordinates: [[[]], [[]]] };
  assert.equal(normalizeTownPolygons(polygon).length, 1);
  assert.equal(normalizeTownPolygons(multi).length, 2);
  assert.throws(() => normalizeTownPolygons({ type: "Point", coordinates: [0, 0] }));
});
