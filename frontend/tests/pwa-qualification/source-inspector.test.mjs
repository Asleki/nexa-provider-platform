import test from "node:test";
import assert from "node:assert/strict";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { inspectDeclaredPwaSources } from "../../src/pwa/qualification/source-inspector.js";
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

test("worker and policy declarations are extracted deterministically", () => {
  const result = inspectDeclaredPwaSources(ROOT);
  assert.equal(result.workerCacheVersion, "nexilabs-shell-v11");
  assert.equal(result.policyCacheVersion, "nexilabs-shell-v11");
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


test("Bundle 12B state assets remain inside the offline shell inventory", () => {
  const result = inspectDeclaredPwaSources(ROOT);
  for (const asset of [
    "./src/map/state/view-state-contracts.js",
    "./src/map/state/view-state-storage.js",
    "./src/map/state/view-state-runtime.js",
    "./src/map/state/world-state-contracts.js",
    "./src/map/state/world-state-store.js",
    "./src/map/state/world-state-runtime.js",
    "./src/map/state/p006-state-integration.js",
  ]) assert.ok(result.workerAssets.includes(asset), asset);
});


test("Bundle 12C NexiLabs shell assets remain inside the offline shell inventory", () => {
  const result = inspectDeclaredPwaSources(ROOT);
  for (const asset of [
    "./src/ui/partials/header.html",
    "./src/ui/partials/footer.html",
    "./src/app/shell/nexilabs-shell.js",
    "./src/app/navigation/application-router.js",
    "./src/ui/navigation/primary-navigation.js",
    "./src/ui/pages/runtime-gateway.js",
    "./src/ui/pages/production-access.js",
  ]) assert.ok(result.workerAssets.includes(asset), asset);
});

test("Bundle 12.0C recovery module remains inside worker-policy shell parity", () => {
  const result = inspectDeclaredPwaSources(ROOT);
  assert.ok(result.workerAssets.includes("./src/app/shell/shell-recovery.js"));
  assert.ok(result.policyAssets.includes("./src/app/shell/shell-recovery.js"));
});
