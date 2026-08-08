import test from "node:test";
import assert from "node:assert/strict";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { inspectDeclaredPwaSources } from "../../src/pwa/qualification/source-inspector.js";
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

test("worker and policy declarations are extracted deterministically", () => {
  const result = inspectDeclaredPwaSources(ROOT);
  assert.equal(result.workerCacheVersion, "novegeo-shell-v9");
  assert.equal(result.policyCacheVersion, "novegeo-shell-v9");
  assert.deepEqual(result.workerAssets, result.policyAssets);
  assert.equal(result.workerOfflineDocument, "./index.html");
});

test("Bundle 12A interaction assets remain inside the offline shell inventory", () => {
  const result = inspectDeclaredPwaSources(ROOT);
  for (const asset of [
    "./src/map/interaction/navigation-state.js",
    "./src/map/interaction/navigation-controller.js",
    "./src/map/interaction/input-bindings.js",
    "./src/map/interaction/map-navigation-discovery.js",
    "./src/map/controls/layer-state.js",
    "./src/map/controls/scale.js",
    "./src/map/selection/coordinate-search.js",
    "./src/map/selection/location-selection.js",
  ]) assert.ok(result.workerAssets.includes(asset), asset);
});
