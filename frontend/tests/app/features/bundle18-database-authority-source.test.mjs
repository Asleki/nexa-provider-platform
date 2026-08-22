import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const shell = readFileSync(resolve(ROOT, "src/app/shell/nexilabs-shell.js"), "utf8");
const live = readFileSync(resolve(ROOT, "src/app/features/novegeo-live-authority-runtime.js"), "utf8");

 test("Bundle 18 shell routes NoveGeo through live database-authority composition", () => {
  assert.match(shell, /mountNoveGeoLiveAuthorityRuntime/);
  assert.doesNotMatch(shell, /import \{ mountNoveGeoFeatureRuntime \}/);
  assert.match(shell, /apiBaseUrl: config\.apiBaseUrl/);
  assert.match(shell, /fetchRef/);
});

test("Bundle 18 live authority gate has no static publication or GeoJSON fallback import", () => {
  assert.match(live, /createLiveWorldBoundaryClient/);
  assert.match(live, /mountNoveGeoFeatureRuntime/);
  assert.doesNotMatch(live, /map\/publication\/|v002-standard|v002-overview|standard\.geojson|overview\.geojson|BUNDLED_WORLD_BOUNDARY_PUBLICATION/);
  assert.match(live, /No bundled sovereign boundary has been substituted/);
});
