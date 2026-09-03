import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const worker = readFileSync(new URL("../../sw.js", import.meta.url), "utf8");
const policy = readFileSync(new URL("../../src/pwa/cache-policy.js", import.meta.url), "utf8");

const requiredAssets = [
  "./styles/novegeo-map-first-v1.css",
  "./src/app/features/novegeo-presentation-provider.js",
  "./src/app/features/novegeo-map-extension-loader.js",
  "./src/map/cartography/semantic-zoom-v2.js",
  "./src/map/cartography/geodesic-scale-v2.js",
  "./src/map/cartography/unified-projection.js",
  "./src/map/cartography/unified-frame-plan.js",
  "./src/map/cartography/unified-frame-renderer.js",
  "./src/map/cartography/presentation-coordinator.js",
  "./public/geography/novegeo/map-extensions/manifest.json",
];

test(".15.10 R2 preserves v17 and caches the complete map-first module graph", () => {
  assert.match(worker, /CACHE_NAME = "nexilabs-shell-v17"/);
  assert.match(policy, /PWA_CACHE_VERSION = "nexilabs-shell-v17"/);
  for (const asset of requiredAssets) {
    assert.ok(worker.includes(`"${asset}"`), `worker missing ${asset}`);
    assert.ok(policy.includes(`"${asset}"`), `policy missing ${asset}`);
  }
  assert.match(worker, /MAP_FIRST_PRESENTATION_SAME_GENERATION_REFRESH_MARKER = "nexilabs-refresh-p006-7-11-15-10-r2"/);
});

test("an existing v17 installation refreshes cached modules and restarts its client", async () => {
  const listeners = new Map();
  const stores = new Map([["nexilabs-shell-v17", new Map()]]);
  let navigations = 0;
  const cache = (name) => ({
    async addAll(assets) { for (const asset of assets) stores.get(name).set(asset, asset); },
    async put(key, value) { stores.get(name).set(key, value); },
    async match(key) { return stores.get(name).get(key); },
  });
  const caches = {
    async keys() { return [...stores.keys()]; },
    async open(name) { if (!stores.has(name)) stores.set(name, new Map()); return cache(name); },
    async delete(name) { return stores.delete(name); },
    async match() { return undefined; },
  };
  const self = {
    location: { origin: "http://127.0.0.1:8765" },
    addEventListener(type, listener) { listeners.set(type, listener); },
    async skipWaiting() {},
    clients: {
      async claim() {},
      async matchAll() { return [{ url: "http://127.0.0.1:8765/#/simulation/novegeo", async navigate() { navigations += 1; } }]; },
    },
  };
  vm.runInNewContext(worker, { self, caches, URL, AbortController, setTimeout, clearTimeout, fetch: async () => { throw new Error("network not expected"); } });
  const run = async (type) => {
    let pending;
    listeners.get(type)({ waitUntil(value) { pending = value; } });
    await pending;
  };
  await run("install");
  assert.ok(stores.has("nexilabs-refresh-p006-7-11-15-10-r2"));
  for (const asset of requiredAssets) assert.ok(stores.get("nexilabs-shell-v17").has(asset));
  await run("activate");
  assert.equal(navigations, 1);
  assert.deepEqual([...stores.keys()], ["nexilabs-shell-v17"]);
});
