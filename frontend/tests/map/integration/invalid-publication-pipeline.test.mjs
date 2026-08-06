import test from "node:test";
import assert from "node:assert/strict";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";
import { createViewport } from "../../../src/map/presentation/viewport.js";
import { qualifyMapCore } from "../../../src/map/validation/qualification.js";

test("malformed governed geometry fails before map rendering", () => {
  const publication = { ...BUNDLED_WORLD_BOUNDARY_PUBLICATION, geometry: { type: "MultiPolygon", coordinates: [[[[0,0],[1,0],[1,1],[0,1]]]] } };
  const viewport = createViewport({ cssWidth: 500, cssHeight: 340, extent: BUNDLED_WORLD_BOUNDARY_PUBLICATION.extent });
  const receipt = qualifyMapCore({ publication, viewport });
  assert.equal(receipt.status, "FAILED");
  assert.ok(receipt.findings.some((finding) => finding.code === "GEOMETRY_STRUCTURE" && !finding.passed));
});
