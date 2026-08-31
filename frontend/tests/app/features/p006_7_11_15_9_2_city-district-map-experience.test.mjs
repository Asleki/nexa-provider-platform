import test from "node:test";
import assert from "node:assert/strict";
import {
  extensionId,
  installNoveGeoMapExtension,
  installNoveGeoCityDistrictMapExperience,
} from "../../../src/app/features/novegeo-city-district-map-experience.js";

test("CITY_DISTRICT extension exports the constrained loader contract", () => {
  assert.equal(extensionId, "nngla-map-extension:city-district:v1");
  assert.equal(typeof installNoveGeoMapExtension, "function");
  assert.equal(typeof installNoveGeoCityDistrictMapExperience, "function");
});
