import test from "node:test";
import assert from "node:assert/strict";
import { NOVEGEO_HYDROLOGY_STANDARD } from "../../../src/map/hydrology/catalog.js";
import { createHydrologyRenderPlan } from "../../../src/map/hydrology/render-plan.js";
import { createViewport } from "../../../src/map/presentation/viewport.js";
import { MapFitMode } from "../../../src/map/presentation/contracts.js";
const viewport=createViewport({cssWidth:420,cssHeight:286,devicePixelRatio:1,padding:24,fitMode:MapFitMode.BOUNDARY,extent:NOVEGEO_HYDROLOGY_STANDARD.extent});
test("P005.3 rivers and lakes map into the governed viewport",()=>{ const p=createHydrologyRenderPlan(NOVEGEO_HYDROLOGY_STANDARD,viewport); assert.equal(p.rivers.length,5); assert.equal(p.lakes.length,3); assert.ok(p.rivers.every(r=>r.points.length>=3)); });
test("Bundle 11.0B render plan exposes invisible confluence references without inventing map labels",()=>{const p=createHydrologyRenderPlan(NOVEGEO_HYDROLOGY_STANDARD,viewport);assert.equal(p.junctions.length,4);for(const j of p.junctions){assert.match(j.junctionId,/^junction:novegeo:j\d{6}$/);assert.ok(Number.isFinite(j.x)&&Number.isFinite(j.y));assert.ok(j.incomingRiverIds.length>=1);}});
