import test from "node:test";
import assert from "node:assert/strict";
import { NOVEGEO_CLIMATE_STANDARD } from "../../../src/map/climate/catalog.js";
import { validateClimatePublication } from "../../../src/map/climate/contracts.js";
test("P005.4 exposes one strong and one larger more powerful rainfall system",()=>{const v=validateClimatePublication(NOVEGEO_CLIMATE_STANDARD);const s=[...v.rainfallSystems].sort((a,b)=>a.relativePower-b.relativePower);assert.equal(s[0].intensityClass,"strong");assert.equal(s[1].intensityClass,"powerful");assert.ok(s[1].peakAnnualRainfallMm>s[0].peakAnnualRainfallMm);assert.ok(s[1].radiusLongitudeDegrees*s[1].radiusLatitudeDegrees>s[0].radiusLongitudeDegrees*s[0].radiusLatitudeDegrees)});
test("Bundle 11.0B rainfall identities are anonymous reference points with invisible irregular fields",()=>{const v=validateClimatePublication(NOVEGEO_CLIMATE_STANDARD);for(const s of v.rainfallSystems){assert.match(s.rainfallSystemId,/^rainfall:novegeo:rs\d{6}$/);assert.equal("name" in s,false);assert.equal(s.fieldModel.type,"irregular_radial_intensity");assert.equal(s.fieldModel.visibleBoundary,false);assert.deepEqual(s.referencePoint,s.center);}});
