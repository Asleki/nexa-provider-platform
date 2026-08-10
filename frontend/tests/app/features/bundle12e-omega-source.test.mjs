import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const css = readFileSync(resolve(ROOT, "styles/app.css"), "utf8");
const runtime = readFileSync(resolve(ROOT, "src/app/features/novegeo-feature-runtime.js"), "utf8");
const main = readFileSync(resolve(ROOT, "src/main.js"), "utf8");
const index = readFileSync(resolve(ROOT, "index.html"), "utf8");

test("Bundle 12E Omega removes the 12E oversized mobile viewport geometry", () => {
  assert.match(css, /\.novegeo-feature-page \[data-role="future-map-viewport"\][\s\S]*width:\s*100%/);
  assert.match(css, /aspect-ratio:\s*16\s*\/\s*11/);
  assert.doesNotMatch(css, /width:\s*max\(100%,\s*48rem\)/);
  assert.doesNotMatch(css, /width:\s*max\(100%,\s*46rem\)/);
  assert.doesNotMatch(css, /translateX\(-50%\)/);
});

test("Bundle 12E Omega owns one resize redraw path for all map presentation layers", () => {
  assert.match(runtime, /mountMapPresentation\(documentRef, \{ observeResize: false \}\)/);
  for (const marker of [
    "mountPhysicalLandPresentation(documentRef)",
    "mountBiospherePresentation(documentRef)",
    "mountHydrologyAtmospherePresentation(documentRef)",
    "mountFullViewportCoordinatePresentation(documentRef)",
    "createNoveGeoResizeCoordinator",
  ]) assert.ok(runtime.includes(marker), marker);
});

test("Bundle 12E Omega retires the 12.0.1E automatic opening-view compensation from browser bootstrap", () => {
  assert.doesNotMatch(main, /installBundle1201EMaintenance|bundle12-0-1e-maintenance/);
  assert.doesNotMatch(index, /bundle12-0-1e-maintenance\.css/);
});
