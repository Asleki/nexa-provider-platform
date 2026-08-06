import test from "node:test";
import assert from "node:assert/strict";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";
import { createViewport } from "../../../src/map/presentation/viewport.js";
import { qualifyMapCore } from "../../../src/map/validation/qualification.js";

test("bundled NoveGeo map core produces a deterministic passing qualification", () => {
  const viewport = createViewport({ cssWidth: 600, cssHeight: 400, extent: BUNDLED_WORLD_BOUNDARY_PUBLICATION.extent });
  const receipt = qualifyMapCore({ publication: BUNDLED_WORLD_BOUNDARY_PUBLICATION, viewport });
  assert.equal(receipt.status, "PASSED");
  assert.equal(receipt.databaseWritesPerformed, 0);
  assert.ok(receipt.findings.every((finding) => finding.passed));
});

test("extent mismatch produces a failed qualification without rendering authority", () => {
  const publication = { ...BUNDLED_WORLD_BOUNDARY_PUBLICATION, extent: { ...BUNDLED_WORLD_BOUNDARY_PUBLICATION.extent, maxLongitude: 44 } };
  const viewport = createViewport({ cssWidth: 600, cssHeight: 400, extent: publication.extent });
  const receipt = qualifyMapCore({ publication, viewport });
  assert.equal(receipt.status, "FAILED");
  assert.ok(receipt.findings.some((finding) => finding.code === "EXTENT_PARITY" && !finding.passed));
});
