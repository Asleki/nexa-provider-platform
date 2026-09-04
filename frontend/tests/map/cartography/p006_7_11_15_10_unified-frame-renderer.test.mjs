import test from "node:test";
import assert from "node:assert/strict";
import { renderUnifiedCartographicFrame } from "../../../src/map/cartography/unified-frame-renderer.js";

function context() {
  return {
    save() {}, restore() {}, beginPath() {}, moveTo() {}, lineTo() {}, closePath() {},
    fill() {}, stroke() {}, setLineDash() {}, arc() {}, fillRect() {}, setTransform() {}, clearRect() {}, clip() {},
    strokeText() {}, fillText() {},
    measureText(text) { return { width: String(text).length * 6 }; },
  };
}

const polygon = { type: "Polygon", coordinates: [[[32,-4],[38,-4],[38,4],[32,4],[32,-4]]] };
const boundary = {
  extent: { minLongitude: 30, minLatitude: -10, maxLongitude: 50, maxLatitude: 10 },
  geometry: { type: "MultiPolygon", coordinates: [[[[30,-10],[50,-10],[50,10],[30,10],[30,-10]]]] },
};
const candidate = (subjectId, displayName, labelClass, longitude, latitude) => ({ subjectId, displayName, labelClass, anchor: { longitude, latitude }, runtimeMode: "simulation", publicationReference: `pub:${subjectId}` });
const country = candidate("country:novegeo", "NoveGeo", "COUNTRY", 40, 0);
const snapshots = {
  REGION: { items: [{ subjectId: "r1", geometry: polygon }], candidates: [candidate("r1", "Region One", "ADMIN_REGION", 35, 0)] },
  CITY: { items: [{ subjectId: "c1", geometry: polygon }], candidates: [candidate("c1", "City One", "ADMIN_CITY", 35, 0)] },
  MUNICIPALITY: { items: [{ subjectId: "m1", geometry: polygon }], candidates: [candidate("m1", "Municipality One", "ADMIN_MUNICIPAL", 36, 0)] },
  CITY_DISTRICT: { items: [{ subjectId: "d1", geometry: polygon }], candidates: [candidate("d1", "District One", "ADMIN_DISTRICT", 35.1, 0)] },
  TOWN: { items: [], candidates: [candidate("t1", "Town One", "TOWN", 35.2, 0)] },
};

const separatedSnapshots = {
  ...snapshots,
  CITY: { items: snapshots.CITY.items, candidates: [candidate("c1", "City One", "ADMIN_CITY", 33, -5)] },
  MUNICIPALITY: { items: snapshots.MUNICIPALITY.items, candidates: [candidate("m1", "Municipality One", "ADMIN_MUNICIPAL", 43, -4)] },
  CITY_DISTRICT: { items: snapshots.CITY_DISTRICT.items, candidates: [candidate("d1", "District One", "ADMIN_DISTRICT", 45, 4)] },
  TOWN: { items: [], candidates: [candidate("t1", "Town One", "TOWN", 47, 6)] },
};

test("unified renderer completes one frame with geometry, symbols, labels and scale", () => {
  const canvas = { style: {}, getContext: () => context() };
  const receipt = renderUnifiedCartographicFrame({
    canvas,
    cssWidth: 720,
    cssHeight: 540,
    devicePixelRatio: 2,
    boundaryPublication: boundary,
    countryCandidate: country,
    snapshots: separatedSnapshots,
    zoom: 3.5,
    navigation: { zoom: 3.5, offsetX: 0, offsetY: 0 },
  });
  assert.equal(receipt.status, "RENDERED");
  assert.ok(receipt.geometryFeatureCount >= 3);
  assert.ok(receipt.settlementSymbolCount >= 2);
  assert.ok(receipt.sourceCandidateCount >= 6);
  assert.ok(receipt.scale.distanceKm > 0);
  assert.ok(receipt.viewport.uniformScale <= receipt.viewport.widthScale + 1e-12);
  assert.ok(receipt.viewport.uniformScale <= receipt.viewport.heightScale + 1e-12);
});


test("portrait, landscape and desktop resizing preserves geographic centre and zoom", () => {
  const makeCanvas = () => ({ style: {}, getContext: () => context() });
  const first = renderUnifiedCartographicFrame({
    canvas: makeCanvas(),
    cssWidth: 360,
    cssHeight: 760,
    boundaryPublication: boundary,
    countryCandidate: country,
    snapshots,
    zoom: 2.25,
    navigation: { zoom: 2.25, offsetX: 36, offsetY: -18 },
  });
  const landscape = renderUnifiedCartographicFrame({
    canvas: makeCanvas(),
    cssWidth: 900,
    cssHeight: 420,
    boundaryPublication: boundary,
    countryCandidate: country,
    snapshots,
    zoom: 2.25,
    navigation: { zoom: 2.25, offsetX: 36, offsetY: -18 },
    preserveGeographicCenter: first.geographicCenter,
  });
  const desktop = renderUnifiedCartographicFrame({
    canvas: makeCanvas(),
    cssWidth: 1440,
    cssHeight: 900,
    boundaryPublication: boundary,
    countryCandidate: country,
    snapshots,
    zoom: 2.25,
    navigation: landscape.navigationUsed,
    preserveGeographicCenter: landscape.geographicCenter,
  });
  for (const receipt of [landscape, desktop]) {
    assert.ok(Math.abs(receipt.geographicCenter.longitude - first.geographicCenter.longitude) < 1e-9);
    assert.ok(Math.abs(receipt.geographicCenter.latitude - first.geographicCenter.latitude) < 1e-9);
    assert.equal(receipt.navigationUsed.zoom, 2.25);
  }
});

test("unified renderer composes governed environment through the same full-frame projection before administration", () => {
  const receipt = renderUnifiedCartographicFrame({
    canvas: { style: {}, getContext: () => context() },
    cssWidth: 390,
    cssHeight: 844,
    boundaryPublication: boundary,
    countryCandidate: country,
    snapshots,
    zoom: 2.25,
    navigation: { zoom: 2.25, offsetX: 12, offsetY: -8 },
  });
  assert.equal(receipt.environment.status, "RENDERED");
  assert.equal(receipt.environment.projectionMode, "UNIFIED");
  assert.ok(receipt.environment.physicalLand.terrainSampleCount > 0);
  assert.ok(receipt.environment.biosphere.vegetationSampleCount >= 200);
  assert.ok(receipt.environment.hydrologyAtmosphere.riverCount >= 4);
  assert.equal(receipt.environment.hydrologyAtmosphere.rainfallSystemCount, 2);
  assert.equal(receipt.environment.coordinates.frameCoverage, "full_viewport");
  assert.equal(receipt.equatorRendered, true);
});

test("renderer draws only settlement symbols whose labels survived decluttering", () => {
  const clustered = {
    REGION: { items: [], candidates: [] },
    CITY: { items: [], candidates: [candidate("c-anchor", "Anchor City", "ADMIN_CITY", 40, 0)] },
    MUNICIPALITY: { items: [], candidates: [] },
    CITY_DISTRICT: { items: [], candidates: [] },
    TOWN: { items: [], candidates: [
      candidate("t-cluster", "Cluster Town", "TOWN", 40, 0),
      candidate("t-free", "Free Town", "TOWN", 46, 6),
    ] },
  };
  const receipt = renderUnifiedCartographicFrame({
    canvas: { style: {}, getContext: () => context() },
    cssWidth: 800,
    cssHeight: 600,
    boundaryPublication: boundary,
    countryCandidate: country,
    snapshots: clustered,
    zoom: 5,
    navigation: { zoom: 5, offsetX: 0, offsetY: 0 },
  });
  assert.ok(receipt.settlementSymbolCandidateCount >= receipt.settlementSymbolCount);
  assert.ok(receipt.settlementSymbolRejectedSubjectIds.includes("t-cluster"));
  assert.equal(receipt.visibleSubjectIds.includes("t-cluster"), false);
  assert.equal(receipt.visibleSubjectIds.includes("c-anchor"), true);
  assert.equal(receipt.visibleSubjectIds.includes("t-free"), true);
});

test("existing environmental layer visibility remains truthful inside the unified renderer", () => {
  const receipt = renderUnifiedCartographicFrame({
    canvas: { style: {}, getContext: () => context() },
    cssWidth: 720,
    cssHeight: 540,
    boundaryPublication: boundary,
    countryCandidate: country,
    snapshots,
    zoom: 2.5,
    navigation: { zoom: 2.5, offsetX: 0, offsetY: 0 },
    environmentalLayerVisibility: {
      physicalLand: false,
      biosphere: true,
      hydrologyAtmosphere: false,
      coordinates: false,
    },
  });
  assert.equal(receipt.environment.physicalLand, null);
  assert.ok(receipt.environment.biosphere);
  assert.equal(receipt.environment.hydrologyAtmosphere, null);
  assert.equal(receipt.environment.coordinates, null);
  assert.equal(receipt.equatorRendered, false);
});

test("renderer receipt keeps non-rendered settlement and label targets addressable for a later selection/zoom milestone", () => {
  const clustered = {
    REGION: { items: [], candidates: [] },
    CITY: { items: [], candidates: [candidate("c-anchor", "Anchor City", "ADMIN_CITY", 40, 0)] },
    MUNICIPALITY: { items: [], candidates: [candidate("m-label", "Municipality Label", "ADMIN_MUNICIPAL", 44, 4)] },
    CITY_DISTRICT: { items: [], candidates: [] },
    TOWN: { items: [], candidates: [candidate("t-cluster", "Cluster Town", "TOWN", 40, 0)] },
  };
  const receipt = renderUnifiedCartographicFrame({
    canvas: { style: {}, getContext: () => context() },
    cssWidth: 800,
    cssHeight: 600,
    boundaryPublication: boundary,
    countryCandidate: country,
    snapshots: clustered,
    zoom: 5,
    navigation: { zoom: 5, offsetX: 0, offsetY: 0 },
  });
  const townTarget = receipt.presentationTargets.find((target) => target.subjectId === "t-cluster");
  const municipalityTarget = receipt.presentationTargets.find((target) => target.subjectId === "m-label");
  assert.ok(townTarget);
  assert.equal(townTarget.interactionKind, "SETTLEMENT");
  assert.equal(townTarget.symbolRendered, false);
  assert.equal(townTarget.labelRendered, false);
  assert.equal(townTarget.symbolRejectedReason, "settlement_label_rejected");
  assert.equal(Number.isFinite(townTarget.x), true);
  assert.equal(Number.isFinite(townTarget.y), true);
  assert.ok(municipalityTarget);
  assert.equal(municipalityTarget.interactionKind, "ADMINISTRATIVE_LABEL");
  assert.equal(municipalityTarget.settlementCapable, false);
  assert.equal(municipalityTarget.symbolRendered, false);
});
