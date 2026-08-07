import test from "node:test";
import assert from "node:assert/strict";
import { NOVEGEO_TERRAIN_STANDARD } from "../../../src/map/terrain/catalog.js";
import { terrainColorForElevation, validateTerrainPublication } from "../../../src/map/terrain/contracts.js";

test("P005.1 terrain publication preserves governed CRS, datum and v002 lineage", () => {
  const terrain = validateTerrainPublication(NOVEGEO_TERRAIN_STANDARD);
  assert.equal(terrain.boundaryVersion, 2);
  assert.equal(terrain.elevationDatum.unit, "metre");
  assert.equal(terrain.runtimeMode, "shared_reference");
  assert.ok(terrain.samples.length > 1000);
});

test("P005.1 elevation palette is deterministic across lowland and mountain bands", () => {
  assert.equal(terrainColorForElevation(100), "#655f54");
  assert.equal(terrainColorForElevation(900), "#9a7f5e");
  assert.equal(terrainColorForElevation(2600), "#d5d0c6");
});
