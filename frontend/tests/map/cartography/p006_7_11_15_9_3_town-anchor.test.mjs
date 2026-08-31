import test from "node:test";
import assert from "node:assert/strict";
import {
  assertPublishedNoveGeoTownSubset,
  createNoveGeoTownLabelCandidate,
  isNoveGeoTownMapItem,
} from "../../../src/map/cartography/town-anchor.js";

const item = Object.freeze({
  subjectId: "NG-PLC-000101",
  family: "PLACE",
  displayName: "Example Town",
  publicationReference: "town-publication:NG-PLC-000101:v1",
  geometryId: "town-footprint:NG-PLC-000101:v1",
  geometryVersion: 1,
  geometryRole: "SETTLEMENT_FOOTPRINT",
  geometryType: "POLYGON",
  geometry: { type: "Polygon", coordinates: [] },
  runtimeEffectScope: "SHARED_REFERENCE",
  classificationCode: "TOWN",
  parentPlaceId: "NG-PLC-000001",
  labelPoint: { type: "Point", coordinates: [31, -11] },
  labelPointAlgorithmId: "algorithm:nngla:town-label-point-on-surface:epsg4326",
  labelPointAlgorithmVersion: 1,
});

test("TOWN map item and label adapter are governed", () => {
  assert.equal(isNoveGeoTownMapItem(item), true);
  assert.equal(assertPublishedNoveGeoTownSubset([item]).length, 1);
  const candidate = createNoveGeoTownLabelCandidate(item, { readRuntime: "simulation" });
  assert.equal(candidate.labelClass, "TOWN");
  assert.equal(candidate.anchor.longitude, 31);
  assert.equal(candidate.anchor.latitude, -11);
});
