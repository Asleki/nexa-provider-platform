import test from "node:test";
import assert from "node:assert/strict";
import { NOVEGEO_LANDFORMS_STANDARD } from "../../../src/map/landforms/catalog.js";
import { createLandformRenderPlan } from "../../../src/map/landforms/render-plan.js";
import { createViewport } from "../../../src/map/presentation/viewport.js";
import { MapFitMode } from "../../../src/map/presentation/contracts.js";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";

test("P005.2 semantic landform features produce a stable overlay plan", () => {
  const viewport=createViewport({cssWidth:640,cssHeight:435,devicePixelRatio:1,padding:30,fitMode:MapFitMode.BOUNDARY,extent:BUNDLED_WORLD_BOUNDARY_PUBLICATION.extent});
  const plan=createLandformRenderPlan(NOVEGEO_LANDFORMS_STANDARD,viewport);
  assert.equal(plan.datasetId,"dataset:novegeo:landforms");
  assert.ok(plan.features.length>=8);
  assert.ok(plan.features.every((feature)=>feature.radius>0&&feature.color));
});
