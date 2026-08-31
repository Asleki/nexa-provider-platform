import test from "node:test";
import assert from "node:assert/strict";
import {
  isNoveGeoMunicipalityMapItem,
  assertPublishedNoveGeoMunicipalitySubset,
  MUNICIPALITY_TARGET_COUNT,
} from "../../../src/map/cartography/municipality-anchor.js";

test("MUNICIPALITY adapter accepts governed ADMINISTRATIVE_AREA records", () => {
  const item = {
    family: "ADMINISTRATIVE_AREA",
    classificationCode: "MUNICIPALITY",
    subjectId: "NG-ADM-000010",
    parentRegionId: "NG-ADM-000001",
  };
  assert.equal(isNoveGeoMunicipalityMapItem(item), true);
  assert.equal(assertPublishedNoveGeoMunicipalitySubset([item]).length, 1);
  assert.equal(MUNICIPALITY_TARGET_COUNT, 24);
});
