import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {dirname,resolve} from "node:path";
import {fileURLToPath} from "node:url";
const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),"../../..");
const main=readFileSync(resolve(ROOT,"src/main.js"),"utf8");

test(".15.4 main composition preserves Bundle22B national geography and appends cartography",()=>{
  assert.match(main,/novegeo-national-geography-experience\.js/);
  assert.match(main,/installNoveGeoNationalGeographyExperience/);
  assert.match(main,/novegeo-cartographic-styling-experience\.js/);
  assert.match(main,/installNoveGeoCartographicStylingExperience/);
});
