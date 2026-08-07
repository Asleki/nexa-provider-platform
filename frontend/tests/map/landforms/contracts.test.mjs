import test from "node:test";
import assert from "node:assert/strict";
import { NOVEGEO_LANDFORMS_STANDARD } from "../../../src/map/landforms/catalog.js";
import { validateLandformPublication } from "../../../src/map/landforms/contracts.js";

test("P005.2 landforms retain terrain lineage and all canonical classes", () => {
  const value=validateLandformPublication(NOVEGEO_LANDFORMS_STANDARD);
  assert.equal(value.properties.terrainDatasetVersion,1);
  assert.deepEqual(new Set(value.features.map((feature)=>feature.properties.landformClass)),new Set(["mountain","valley","plain","plateau"]));
  assert.ok(value.features.every((feature)=>String(feature.id).startsWith("landform:novegeo:")));
});
