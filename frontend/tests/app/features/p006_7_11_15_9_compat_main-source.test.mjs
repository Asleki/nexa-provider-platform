import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");

test("generic map-extension loader is activated only after the locked CITY bootstrap attempt", () => {
  const source = readFileSync(resolve(ROOT, "src/main.js"), "utf8");
  assert.match(source, /novegeo-region-map-experience\.js/);
  assert.match(source, /novegeo-city-map-experience\.js/);
  assert.match(source, /novegeo-map-extension-loader\.js/);
  assert.ok(source.indexOf("novegeo-region-map-experience.js") < source.indexOf("novegeo-city-map-experience.js"));
  assert.ok(source.indexOf("novegeo-city-map-experience.js") < source.indexOf("novegeo-map-extension-loader.js"));
  assert.match(source, /installNoveGeoMapExtensions/);
  assert.doesNotMatch(source, /municipality-map-experience\.js/);
  assert.doesNotMatch(source, /city-district-map-experience\.js/);
  assert.doesNotMatch(source, /town-map-experience\.js/);
  assert.doesNotMatch(source, /roadmap/i);
});
