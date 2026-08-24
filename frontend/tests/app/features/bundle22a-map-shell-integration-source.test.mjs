import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const shellSource = readFileSync(resolve(ROOT, "src/app/shell/nexilabs-shell.js"), "utf8");
const mapShellSource = readFileSync(resolve(ROOT, "src/map/controls/novegeo-map-shell.js"), "utf8");
const css = readFileSync(resolve(ROOT, "styles/novegeo-map-shell-v1.css"), "utf8");
const lockedRuntime = readFileSync(resolve(ROOT, "src/app/features/novegeo-feature-runtime.js"), "utf8");

 test("Bundle 22A is an additive shell adapter and keeps Bundle 18 live authority composition", () => {
  assert.match(shellSource, /mountNoveGeoLiveAuthorityRuntime/);
  assert.match(shellSource, /mountNoveGeoMapShellHardeningRuntime/);
  assert.doesNotMatch(mapShellSource, /mountMapPresentation|createMapNavigationController|createLiveNnglaReadClient/);
  assert.match(mapShellSource, /Reference layers/);
  assert.match(mapShellSource, /National geography/);
  assert.match(mapShellSource, /Developer & authority details/);
});

test("Bundle 22A CSS makes permanent tools static and tools sheet non-overlay", () => {
  assert.match(css, /\.novegeo-tool-rail[\s\S]*position: static !important/);
  assert.match(css, /\.novegeo-feature-controls[\s\S]*position: static !important/);
  assert.match(css, /data-open-panel="false"[\s\S]*display: none !important/);
});

test("Bundle 22A does not rewrite the locked Bundle 12E six-control source contract", () => {
  for (const action of ["zoom-out", "zoom-in", "search", "layers", "info", "reset"]) {
    assert.ok(lockedRuntime.includes(`\"${action}\"`), action);
  }
});
