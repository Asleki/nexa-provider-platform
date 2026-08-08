import test from "node:test";
import assert from "node:assert/strict";
import { NOVEGEO_CLIMATE_STANDARD } from "../../../src/map/climate/catalog.js";
import { createClimateRenderPlan } from "../../../src/map/climate/render-plan.js";
import { createViewport } from "../../../src/map/presentation/viewport.js";
import { MapFitMode } from "../../../src/map/presentation/contracts.js";
const viewport=createViewport({cssWidth:420,cssHeight:286,devicePixelRatio:1,padding:24,fitMode:MapFitMode.BOUNDARY,extent:NOVEGEO_CLIMATE_STANDARD.extent});
test("P005.4 climate plan maps rainfall cells, two systems and wind samples",()=>{const p=createClimateRenderPlan(NOVEGEO_CLIMATE_STANDARD,viewport); assert.ok(p.cells.length>=250); assert.equal(p.rainfallSystems.length,2); assert.ok(p.winds.length>20); const strong=p.rainfallSystems.find(x=>x.intensityClass==="strong"), powerful=p.rainfallSystems.find(x=>x.intensityClass==="powerful"); assert.ok(powerful.radiusX*powerful.radiusY>strong.radiusX*strong.radiusY);});
