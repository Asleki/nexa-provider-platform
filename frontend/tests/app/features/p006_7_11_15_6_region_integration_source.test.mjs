import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),"../../..");
const main=readFileSync(resolve(ROOT,"src/main.js"),"utf8");
test("P006.7.11.15.6 mounts REGION map experience additively beside locked national geography/cartography",()=>{
  assert.match(main,/novegeo-national-geography-experience\.js/);
  assert.match(main,/novegeo-cartographic-styling-experience\.js/);
  assert.match(main,/novegeo-region-map-experience\.js/);
  assert.match(main,/installNoveGeoRegionMapExperience/);
  assert.doesNotMatch(main,/roadmap/i);
});
