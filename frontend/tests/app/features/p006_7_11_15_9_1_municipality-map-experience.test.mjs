import test from "node:test";
import assert from "node:assert/strict";
import {
  installNoveGeoMapExtension,
  installNoveGeoMunicipalityMapExperience,
} from "../../../src/app/features/novegeo-municipality-map-experience.js";

test("MUNICIPALITY experience exports CM1 install contract", () => {
  assert.equal(typeof installNoveGeoMapExtension, "function");
  assert.equal(typeof installNoveGeoMunicipalityMapExperience, "function");
});
