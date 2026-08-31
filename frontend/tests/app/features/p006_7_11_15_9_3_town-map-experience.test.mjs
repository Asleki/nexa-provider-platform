import test from "node:test";
import assert from "node:assert/strict";
import {
  extensionId,
  installNoveGeoMapExtension,
  installNoveGeoTownMapExperience,
} from "../../../src/app/features/novegeo-town-map-experience.js";

test("TOWN extension exports the constrained loader contract", () => {
  assert.equal(extensionId, "nngla-map-extension:town:v1");
  assert.equal(typeof installNoveGeoMapExtension, "function");
  assert.equal(typeof installNoveGeoTownMapExperience, "function");
});
