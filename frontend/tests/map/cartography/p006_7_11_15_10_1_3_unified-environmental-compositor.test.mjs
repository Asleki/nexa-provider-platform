import test from "node:test";
import assert from "node:assert/strict";
import {
  createUnifiedEnvironmentalLayerVisibility,
  renderUnifiedEnvironmentalComposition,
  UnifiedEnvironmentalLayerKey,
} from "../../../src/map/cartography/unified-environmental-compositor.js";

const boundary = {
  extent: { minLongitude: 30, minLatitude: -10, maxLongitude: 50, maxLatitude: 10 },
  geometry: { type: "MultiPolygon", coordinates: [[[[30,-10],[50,-10],[50,10],[30,10],[30,-10]]]] },
};

function context() {
  const calls = [];
  return {
    calls,
    save() {}, restore() {}, beginPath() {}, moveTo(x,y) { calls.push(["moveTo",x,y]); }, lineTo(x,y) { calls.push(["lineTo",x,y]); }, closePath() {},
    clip() {}, fill() {}, stroke() {}, setLineDash() {}, arc() {}, fillRect() {},
  };
}

test("unified compositor renders the complete existing environmental stack through the supplied projection", () => {
  const ctx = context();
  const seen = [];
  const project = (longitude, latitude) => { seen.push([longitude, latitude]); return { x: longitude * 10, y: 200 - latitude * 10 }; };
  const receipt = renderUnifiedEnvironmentalComposition({
    context: ctx,
    cssWidth: 720,
    cssHeight: 540,
    boundaryPublication: boundary,
    project,
  });
  assert.equal(receipt.status, "RENDERED");
  assert.equal(receipt.projectionMode, "UNIFIED");
  assert.ok(receipt.physicalLand.terrainSampleCount > 0);
  assert.ok(receipt.physicalLand.landformFeatureCount > 0);
  assert.ok(receipt.biosphere.vegetationSampleCount >= 200);
  assert.ok(receipt.hydrologyAtmosphere.riverCount >= 4);
  assert.ok(receipt.hydrologyAtmosphere.lakeCount >= 2);
  assert.equal(receipt.hydrologyAtmosphere.rainfallSystemCount, 2);
  assert.equal(receipt.coordinates.equatorRendered, true);
  assert.ok(seen.some(([longitude, latitude]) => longitude === 40 && latitude === 0));
});

test("existing P006 environmental visibility keys remain independently truthful in unified mode", () => {
  const visibility = createUnifiedEnvironmentalLayerVisibility({
    [UnifiedEnvironmentalLayerKey.PHYSICAL_LAND]: false,
    [UnifiedEnvironmentalLayerKey.BIOSPHERE]: true,
    [UnifiedEnvironmentalLayerKey.HYDROLOGY_ATMOSPHERE]: false,
    [UnifiedEnvironmentalLayerKey.COORDINATES]: false,
  });
  const receipt = renderUnifiedEnvironmentalComposition({
    context: context(),
    cssWidth: 640,
    cssHeight: 435,
    boundaryPublication: boundary,
    project: (longitude, latitude) => ({ x: longitude, y: latitude }),
    layerVisibility: visibility,
  });
  assert.equal(receipt.physicalLand, null);
  assert.ok(receipt.biosphere);
  assert.equal(receipt.hydrologyAtmosphere, null);
  assert.equal(receipt.coordinates, null);
  assert.equal(receipt.equatorRendered, false);
});

test("the compositor never owns domain identity and exposes only source dataset receipts", () => {
  const receipt = renderUnifiedEnvironmentalComposition({
    context: context(), cssWidth: 800, cssHeight: 500, boundaryPublication: boundary,
    project: (longitude, latitude) => ({ x: longitude * 2, y: latitude * 2 }),
  });
  const serialized = JSON.stringify(receipt);
  assert.match(serialized, /dataset:novegeo:terrain:elevation/);
  assert.match(serialized, /dataset:novegeo:hydrology:surface-water/);
  assert.match(serialized, /dataset:novegeo:climate:baseline/);
  assert.doesNotMatch(serialized, /riverName|lakeName|rainfallSystemName/);
});

test("unified coordinate presentation preserves the locked predecessor graticule and Equator styling constants", () => {
  const calls = [];
  const ctx = {
    save() {}, restore() {}, beginPath() {}, moveTo() {}, lineTo() {}, closePath() {}, clip() {}, fill() {},
    stroke() { calls.push(["stroke", this.strokeStyle, this.lineWidth, this._dash]); },
    setLineDash(value) { this._dash = [...value]; }, arc() {}, fillRect() {},
  };
  renderUnifiedEnvironmentalComposition({
    context: ctx,
    cssWidth: 720,
    cssHeight: 540,
    boundaryPublication: boundary,
    project: (longitude, latitude) => ({ x: longitude * 10, y: 200 - latitude * 10 }),
    layerVisibility: { physicalLand: false, biosphere: false, hydrologyAtmosphere: false, coordinates: true },
  });
  assert.ok(calls.some(([, strokeStyle, lineWidth, dash]) => strokeStyle === "rgba(203, 213, 225, 0.24)" && lineWidth === 1 && Array.isArray(dash) && dash.length === 0));
  assert.ok(calls.some(([, strokeStyle, lineWidth, dash]) => strokeStyle === "#19d3e6" && lineWidth === 2 && JSON.stringify(dash) === JSON.stringify([7, 5])));
});
