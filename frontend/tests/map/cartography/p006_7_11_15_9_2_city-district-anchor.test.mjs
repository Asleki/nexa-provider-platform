import test from "node:test";
import assert from "node:assert/strict";
import {
  assertPublishedNoveGeoCityDistrictSubset,
  createNoveGeoCityDistrictLabelCandidate,
  isNoveGeoCityDistrictMapItem,
} from "../../../src/map/cartography/city-district-anchor.js";

const item = Object.freeze({
  subjectId: "NG-ADM-000101",
  family: "ADMINISTRATIVE_AREA",
  displayName: "Example District",
  publicationReference: "city-district-publication:NG-ADM-000101:v1",
  geometryId: "city-district-geometry:NG-ADM-000101:v1",
  geometryVersion: 1,
  geometryRole: "ADMINISTRATIVE_BOUNDARY",
  geometryType: "POLYGON",
  geometry: { type: "Polygon", coordinates: [] },
  runtimeEffectScope: "SHARED_REFERENCE",
  classificationCode: "CITY_DISTRICT",
  parentCityId: "NG-ADM-000009",
  partitionStatus: "COMPLETE",
  labelPoint: { type: "Point", coordinates: [30, -10] },
  labelPointAlgorithmId: "algorithm:nngla:city-district-label-point-on-surface:epsg4326",
  labelPointAlgorithmVersion: 1,
});

test("CITY_DISTRICT map item and label adapter are governed", () => {
  assert.equal(isNoveGeoCityDistrictMapItem(item), true);
  assert.equal(assertPublishedNoveGeoCityDistrictSubset([item]).length, 1);
  const candidate = createNoveGeoCityDistrictLabelCandidate(item, { readRuntime: "simulation" });
  assert.equal(candidate.labelClass, "ADMIN_DISTRICT");
  assert.equal(candidate.anchor.longitude, 30);
  assert.equal(candidate.anchor.latitude, -10);
});
