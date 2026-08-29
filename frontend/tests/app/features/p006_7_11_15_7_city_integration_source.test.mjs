import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),"../../..");

test("P006.7.11.15.7 mounts CITY experience additively beside REGION experience",()=>{
  const source=readFileSync(resolve(ROOT,"src/main.js"),"utf8");
  assert.match(source,/novegeo-region-map-experience\.js/);
  assert.match(source,/novegeo-city-map-experience\.js/);
  assert.ok(source.indexOf("novegeo-region-map-experience.js") < source.indexOf("novegeo-city-map-experience.js"));
  assert.doesNotMatch(source,/roadmap/i);
});
