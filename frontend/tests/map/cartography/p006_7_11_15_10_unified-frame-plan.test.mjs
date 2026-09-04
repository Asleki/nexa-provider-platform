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

test("accepted CITY and TOWN labels accept only their matching settlement symbols", () => {
  const cityLabel = { subjectId: "c1", priority: 820, x: 80, y: 70, style: { collisionPaddingPx: 2 } };
  const townLabel = { subjectId: "t1", priority: 620, x: 180, y: 170, style: { collisionPaddingPx: 2 } };
  const symbols = [
    { subjectId: "c1", x: 80, y: 80, style: { radiusPx: 3, clearancePx: 4 } },
    { subjectId: "t1", x: 180, y: 180, style: { radiusPx: 2, clearancePx: 3 } },
  ];
  const result = declutterUnifiedLabels([
    { label: cityLabel, metrics: { width: 40, height: 12 } },
    { label: townLabel, metrics: { width: 40, height: 12 } },
  ], symbols);
  assert.deepEqual(result.acceptedSymbols.map((symbol) => symbol.subjectId).sort(), ["c1", "t1"]);
  assert.equal(result.rejectedSymbols.length, 0);
});

test("rejected settlement labels reject their point and cannot leave an invisible collision hole", () => {
  const adminLabel = { subjectId: "d1", priority: 900, x: 100, y: 100, style: { collisionPaddingPx: 2 } };
  const cityLabel = { subjectId: "c1", priority: 800, x: 100, y: 70, style: { collisionPaddingPx: 2 } };
  const citySymbol = { subjectId: "c1", x: 100, y: 100, style: { radiusPx: 4, clearancePx: 5 } };
  const result = declutterUnifiedLabels([
    { label: adminLabel, metrics: { width: 50, height: 12 } },
    { label: cityLabel, metrics: { width: 40, height: 10 } },
  ], [citySymbol]);
  assert.equal(result.accepted.some((item) => item.label.subjectId === "d1"), true);
  assert.equal(result.rejected.some((item) => item.label.subjectId === "c1"), true);
  assert.equal(result.acceptedSymbols.some((symbol) => symbol.subjectId === "c1"), false);
  assert.equal(result.rejectedSymbols.some((item) => item.symbol.subjectId === "c1"), true);
});

test("a settlement symbol with no zoom-eligible label is never rendered anonymously", () => {
  const orphan = { subjectId: "orphan", x: 100, y: 100, style: { radiusPx: 3, clearancePx: 4 } };
  const result = declutterUnifiedLabels([], [orphan]);
  assert.equal(result.acceptedSymbols.length, 0);
  assert.equal(result.rejectedSymbols[0].reason, "settlement_label_unavailable");
});

test("presentation targets preserve stable identities and projected anchors for future selection without enabling interaction now", () => {
  const plan = createUnifiedFramePlan({
    boundaryPublication: boundary,
    countryCandidate: country,
    snapshots,
    zoom: 2.1,
    project: (longitude, latitude) => ({ x: longitude * 10, y: latitude * 10 + 100 }),
  });
  const townTarget = plan.presentationTargets.find((target) => target.subjectId === "t1");
  const municipalityTarget = plan.presentationTargets.find((target) => target.subjectId === "m1");
  assert.ok(townTarget);
  assert.equal(townTarget.interactionKind, "SETTLEMENT");
  assert.equal(townTarget.settlementCapable, true);
  assert.equal(townTarget.labelEligible, false);
  assert.equal(townTarget.symbolEligible, false);
  assert.equal(townTarget.publicationReference, "publication:t1");
  assert.equal(Number.isFinite(townTarget.x), true);
  assert.equal(Number.isFinite(townTarget.y), true);
  assert.ok(municipalityTarget);
  assert.equal(municipalityTarget.interactionKind, "ADMINISTRATIVE_LABEL");
  assert.equal(municipalityTarget.settlementCapable, false);
  assert.equal(municipalityTarget.symbolEligible, false);
});
