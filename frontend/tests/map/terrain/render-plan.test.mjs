import test from "node:test";
import assert from "node:assert/strict";
import { NOVEGEO_TERRAIN_STANDARD } from "../../../src/map/terrain/catalog.js";
import { createTerrainRenderPlan } from "../../../src/map/terrain/render-plan.js";
import { createViewport } from "../../../src/map/presentation/viewport.js";
import { MapFitMode } from "../../../src/map/presentation/contracts.js";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";

test("P005.1 terrain samples map into the governed P004 viewport", () => {
  const viewport=createViewport({cssWidth:640,cssHeight:435,devicePixelRatio:1,padding:30,fitMode:MapFitMode.BOUNDARY,extent:BUNDLED_WORLD_BOUNDARY_PUBLICATION.extent});
  const plan=createTerrainRenderPlan(NOVEGEO_TERRAIN_STANDARD,viewport);
  assert.equal(plan.datasetId,"dataset:novegeo:terrain:elevation");
  assert.ok(plan.cellWidth>0 && plan.cellHeight>0);
  assert.equal(plan.samples.length,NOVEGEO_TERRAIN_STANDARD.samples.length);
  assert.ok(plan.samples.every((sample)=>Number.isFinite(sample.x)&&Number.isFinite(sample.y)));
});
