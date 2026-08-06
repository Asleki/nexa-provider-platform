import test from "node:test";
import assert from "node:assert/strict";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";
import { createViewport } from "../../../src/map/presentation/viewport.js";
import { qualifyMapCore } from "../../../src/map/validation/qualification.js";

test("map-core qualification remains valid across mobile and desktop viewports", () => {
  for (const [width, height] of [[320,260],[768,522],[1440,979]]) {
    const viewport = createViewport({ cssWidth: width, cssHeight: height, extent: BUNDLED_WORLD_BOUNDARY_PUBLICATION.extent });
    assert.equal(qualifyMapCore({ publication: BUNDLED_WORLD_BOUNDARY_PUBLICATION, viewport }).status, "PASSED");
  }
});
