import test from "node:test";
import assert from "node:assert/strict";
import { createUniformProjectedViewport } from "../../../src/map/cartography/unified-projection.js";
import { createGeodesicScaleModel, geodesicDistanceKm } from "../../../src/map/cartography/geodesic-scale-v2.js";

const extent = { minLongitude: 30, minLatitude: -10, maxLongitude: 50, maxLatitude: 10 };

test("geodesic distance follows latitude-aware great-circle sampling", () => {
  const equator = geodesicDistanceKm({ longitude: 0, latitude: 0 }, { longitude: 1, latitude: 0 });
  const highLatitude = geodesicDistanceKm({ longitude: 0, latitude: 60 }, { longitude: 1, latitude: 60 });
  assert.ok(equator > highLatitude);
});

test("scale presents one metric distance and its imperial conversion", () => {
  const viewport = createUniformProjectedViewport({ cssWidth: 720, cssHeight: 500, padding: 20, extent });
  const model = createGeodesicScaleModel({ viewport, navigation: { zoom: 2, offsetX: 0, offsetY: 0 } });
  assert.match(model.metricLabel, / km$/);
  assert.match(model.imperialLabel, / mi$/);
  assert.ok(model.widthPx >= 24);
  assert.equal(model.approximation, "screen_sampled_geodesic_at_viewport_centre");
});
