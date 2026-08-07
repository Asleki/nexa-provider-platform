import test from "node:test";
import assert from "node:assert/strict";
import {
  NOVEGEO_V002_PUBLICATION_MANIFEST,
  listWorldBoundaryRepresentations,
  selectWorldBoundaryPublication,
} from "../../../src/map/publication/catalog.js";

test("P004.M1.5 activates governed v002 with standard default and overview alternative", () => {
  assert.equal(NOVEGEO_V002_PUBLICATION_MANIFEST.boundaryVersion, 2);
  assert.equal(NOVEGEO_V002_PUBLICATION_MANIFEST.defaultResolution, "standard");
  assert.deepEqual(listWorldBoundaryRepresentations().map((item) => item.resolutionClass), ["overview", "standard"]);
  const standard = selectWorldBoundaryPublication();
  const overview = selectWorldBoundaryPublication("overview");
  assert.equal(standard.boundaryVersion, 2);
  assert.equal(standard.resolutionClass, "standard");
  assert.equal(standard.derivativeVertexCount, 493);
  assert.equal(overview.derivativeVertexCount, 197);
  assert.equal(standard.polygonCount, 6);
  assert.equal(standard.offshoreIslandCount, 5);
});

test("explicit unsupported resolution is rejected rather than silently substituted", () => {
  assert.throws(() => selectWorldBoundaryPublication("street"), /unsupported map resolution/);
});
