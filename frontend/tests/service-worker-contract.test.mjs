import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const worker = readFileSync(resolve(ROOT, "sw.js"), "utf8");
const policy = readFileSync(resolve(ROOT, "src/pwa/cache-policy.js"), "utf8");

test("service worker implements install, activate, message and fetch lifecycles", () => {
  for (const event of ["install", "activate", "message", "fetch"]) {
    assert.ok(worker.includes(`addEventListener("${event}"`), event);
  }
  assert.match(worker, /cache\.addAll\(APP_SHELL\)/);
  assert.match(worker, /self\.clients\.claim\(\)/);
  assert.match(worker, /self\.skipWaiting\(\)/);
});

test("offline navigation fallback and same-origin GET boundary are explicit", () => {
  assert.match(worker, /request\.method !== "GET"/);
  assert.match(worker, /url\.origin !== self\.location\.origin/);
  assert.match(worker, /request\.mode === "navigate"/);
  assert.match(worker, /caches\.match\(OFFLINE_URL\)/);
});

test("cache version and shell inventory are versioned", () => {
  assert.match(policy, /PWA_CACHE_VERSION = "nexilabs-shell-v16"/);
  assert.match(policy, /APPLICATION_SHELL_ASSETS/);
  assert.match(worker, /CACHE_NAME = "nexilabs-shell-v16"/);
  assert.match(worker, /keys\.filter\(\(key\) => key !== CACHE_NAME\)/);
});

test("Bundle 12A navigation and discovery modules are pre-cached", () => {
  for (const marker of [
    "./src/map/interaction/map-navigation-discovery.js",
    "./src/map/controls/layer-state.js",
    "./src/map/selection/coordinate-search.js",
  ]) {
    assert.ok(worker.includes(marker), marker);
    assert.ok(policy.includes(marker), marker);
  }
});


test("Bundle 12B persistent and dynamic state modules are pre-cached", () => {
  for (const marker of [
    "./src/map/state/view-state-runtime.js",
    "./src/map/state/world-state-store.js",
    "./src/map/state/p006-state-integration.js",
  ]) {
    assert.ok(worker.includes(marker), marker);
    assert.ok(policy.includes(marker), marker);
  }
});


test("Bundle 12C shared NexiLabs shell modules are pre-cached", () => {
  for (const marker of [
    "./src/ui/partials/header.html",
    "./src/ui/partials/footer.html",
    "./src/app/shell/nexilabs-shell.js",
    "./src/ui/pages/runtime-gateway.js",
    "./src/ui/pages/production-access.js",
  ]) {
    assert.ok(worker.includes(marker), marker);
    assert.ok(policy.includes(marker), marker);
  }
});

test("Bundle 12.0C navigation recovery has a bounded network wait and cached fallback", () => {
  assert.match(worker, /NAVIGATION_NETWORK_TIMEOUT_MS = 1800/);
  assert.match(worker, /navigationResponse\(request\)/);
  assert.match(worker, /controller\.abort\(\)/);
  assert.match(worker, /caches\.match\(request\)/);
});

test("Bundle 12.0C shell recovery module is pre-cached", () => {
  const marker = "./src/app/shell/shell-recovery.js";
  assert.ok(worker.includes(marker), marker);
  assert.ok(policy.includes(marker), marker);
});


test("Bundle 12E Simulation/NoveGeo entry assets are pre-cached without private registry or database material", () => {
  for (const marker of [
    "./src/ui/pages/simulation-workspace.js",
    "./src/ui/pages/novegeo-feature.js",
    "./src/app/features/novegeo-feature-runtime.js",
  ]) {
    assert.ok(worker.includes(marker), marker);
    assert.ok(policy.includes(marker), marker);
  }
  assert.doesNotMatch(worker, /PGPASSWORD|development\/auth\/private|database\/seeds/);
});


test("Bundle 12.0E activates only after a complete shell install and restarts stale controlled clients", () => {
  assert.match(worker, /await cache\.addAll\(APP_SHELL\)/);
  assert.match(worker, /await self\.skipWaiting\(\)/);
  assert.match(worker, /previousShellKeys/);
  assert.match(worker, /self\.clients\.matchAll\(\{ type: "window", includeUncontrolled: true \}\)/);
  assert.match(worker, /client\.navigate\(client\.url\)/);
  assert.match(worker, /previousShellKeys\.length > 0/);
});




test("Bundle 12E Omega pre-caches normalized geometry and retires 12.0.1E compensation assets", () => {
  const geometry = "./src/app/features/novegeo-feature-geometry.js";
  assert.ok(worker.includes(geometry), geometry);
  assert.ok(policy.includes(geometry), geometry);
  for (const retired of [
    "./styles/bundle12-0-1e-maintenance.css",
    "./src/app/features/bundle12-0-1e-maintenance.js",
  ]) {
    assert.equal(worker.includes(retired), false, retired);
    assert.equal(policy.includes(retired), false, retired);
  }
});


test("P006.UI.16 pre-caches every manifest icon and publishes one v16 shell generation", () => {
  for (const marker of [
    "./public/brand/nexilabs/pwa/nexilabs_icon_192x192.png",
    "./public/brand/nexilabs/pwa/nexilabs_icon_512x512.png",
    "./public/brand/nexilabs/pwa/nexilabs_maskable_192x192.png",
    "./public/brand/nexilabs/pwa/nexilabs_maskable_512x512.png",
  ]) {
    assert.ok(worker.includes(marker), marker);
    assert.ok(policy.includes(marker), marker);
  }
});
