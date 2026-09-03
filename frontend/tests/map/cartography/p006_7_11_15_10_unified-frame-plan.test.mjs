import test from "node:test";
import assert from "node:assert/strict";
import { createUnifiedFramePlan, declutterUnifiedLabels } from "../../../src/map/cartography/unified-frame-plan.js";

const boundary = {
  extent: { minLongitude: 30, minLatitude: -10, maxLongitude: 50, maxLatitude: 10 },
  geometry: { type: "MultiPolygon", coordinates: [[[[30,-10],[50,-10],[50,10],[30,10],[30,-10]]]] },
};
const candidate = (subjectId, displayName, labelClass, longitude, latitude) => ({
  subjectId, displayName, labelClass,
  anchor: { longitude, latitude },
  runtimeMode: "simulation",
  publicationReference: `publication:${subjectId}`,
});
const country = candidate("country:novegeo", "NoveGeo", "COUNTRY", 40, 0);
const snapshots = {
  REGION: { items: [], candidates: [candidate("r1", "Region", "ADMIN_REGION", 38, 0)] },
  CITY: { items: [], candidates: [candidate("c1", "City", "ADMIN_CITY", 40, 0)] },
  MUNICIPALITY: { items: [], candidates: [candidate("m1", "Municipality", "ADMIN_MUNICIPAL", 42, 0)] },
  CITY_DISTRICT: { items: [], candidates: [candidate("d1", "District", "ADMIN_DISTRICT", 40.1, 0)] },
  TOWN: { items: [], candidates: [candidate("t1", "Town", "TOWN", 40.15, 0)] },
};

test("semantic visibility never re-enables a disabled layer", () => {
  const plan = createUnifiedFramePlan({
    boundaryPublication: boundary,
    countryCandidate: country,
    snapshots,
    zoom: 5,
    userLayerVisibility: { TOWN: false },
    project: (longitude, latitude) => ({ x: longitude * 10, y: latitude * 10 + 100 }),
  });
  assert.equal(plan.labels.some((label) => label.subjectId === "t1"), false);
  assert.equal(plan.symbols.some((symbol) => symbol.subjectId === "t1"), false);
});

test("global collision rejects labels across different governed layers", () => {
  const plan = createUnifiedFramePlan({
    boundaryPublication: boundary,
    countryCandidate: country,
    snapshots,
    zoom: 5,
    project: () => ({ x: 100, y: 100 }),
  });
  const measured = plan.labels.map((label) => ({ label, metrics: { width: 60, height: 14 } }));
  const collision = declutterUnifiedLabels(measured, []);
  assert.ok(collision.accepted.length >= 1);
  assert.ok(collision.rejected.length >= 1);
  const classes = new Set([...collision.accepted, ...collision.rejected].map((item) => item.label.layerKey));
  assert.ok(classes.has("CITY"));
  assert.ok(classes.has("CITY_DISTRICT"));
});

test("settlement symbols reserve screen-space clearance for unrelated labels", () => {
  const cityLabel = { subjectId: "c1", priority: 800, x: 100, y: 80, style: { collisionPaddingPx: 2 } };
  const districtLabel = { subjectId: "d1", priority: 700, x: 100, y: 100, style: { collisionPaddingPx: 2 } };
  const symbol = { subjectId: "c1", x: 100, y: 100, style: { radiusPx: 4, clearancePx: 5 } };
  const result = declutterUnifiedLabels([
    { label: cityLabel, metrics: { width: 30, height: 10 } },
    { label: districtLabel, metrics: { width: 30, height: 10 } },
  ], [symbol]);
  assert.equal(result.rejected.some((item) => item.label.subjectId === "d1" && item.reason === "settlement_symbol_clearance"), true);
});
