import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";

const ROOT = process.cwd();
const workerPath = path.join(ROOT, "frontend", "sw.js");
const policyPath = path.join(ROOT, "frontend", "src", "pwa", "cache-policy.js");

const worker = fs.readFileSync(workerPath, "utf8");
const policy = fs.readFileSync(policyPath, "utf8");

const REQUIRED_CURRENT_ASSETS = Object.freeze([
  "./src/app/features/novegeo-national-geography-experience.js",
  "./src/map/nngla/national-map-client.js",
  "./src/map/nngla/national-map-contracts.js",
  "./src/map/nngla/national-map-state.js",
  "./styles/novegeo-cartography-v1.css",
  "./src/app/features/novegeo-cartographic-styling-experience.js",
  "./src/map/cartography/contracts.js",
  "./src/map/cartography/style-catalog.js",
  "./src/map/cartography/country-anchor.js",
  "./src/map/cartography/label-plan.js",
  "./src/map/cartography/collision.js",
  "./src/map/cartography/label-renderer.js",
  "./src/map/cartography/cartographic-overlay.js",
]);

function parseAssets(source, declaration) {
  const start = source.indexOf(declaration);
  assert.notEqual(start, -1, `${declaration} missing`);
  const tail = source.slice(start);
  const open = tail.indexOf("[");
  const close = tail.indexOf("]");
  assert.ok(open >= 0 && close > open, `${declaration} array missing`);
  return [...tail.slice(open + 1, close).matchAll(/"([^"]+)"/g)].map((m) => m[1]);
}

function makeHarness(initialCacheNames = []) {
  const listeners = new Map();
  const stores = new Map();
  const navigations = [];
  let claimed = 0;
  let skipped = 0;

  function cacheObject(name) {
    if (!stores.has(name)) stores.set(name, new Map());
    const content = stores.get(name);
    return {
      async addAll(assets) {
        for (const asset of assets) {
          content.set(asset, { asset, clone() { return this; } });
        }
      },
      async put(asset, response) { content.set(asset, response); },
      async match(asset) {
        const key = typeof asset === "string" ? asset : asset.url;
        return content.get(key);
      },
    };
  }

  for (const name of initialCacheNames) stores.set(name, new Map());

  const caches = {
    async open(name) { return cacheObject(name); },
    async keys() { return [...stores.keys()]; },
    async delete(name) { return stores.delete(name); },
    async match(request) {
      for (const content of stores.values()) {
        const key = typeof request === "string" ? request : request.url;
        if (content.has(key)) return content.get(key);
      }
      return undefined;
    },
  };

  const self = {
    location: { origin: "http://127.0.0.1:8765" },
    addEventListener(type, fn) { listeners.set(type, fn); },
    async skipWaiting() { skipped += 1; },
    clients: {
      async claim() { claimed += 1; },
      async matchAll() {
        return [
          {
            url: "http://127.0.0.1:8765/#/simulation/novegeo",
            async navigate(url) { navigations.push(url); },
          },
          {
            url: "https://external.example/",
            async navigate(url) { navigations.push(url); },
          },
        ];
      },
    },
  };

  vm.runInNewContext(worker, {
    self, caches, URL, AbortController, setTimeout, clearTimeout,
    fetch: async () => { throw new Error("network not expected"); },
  });

  async function run(type) {
    let promise;
    listeners.get(type)({ waitUntil(value) { promise = value; } });
    await promise;
  }

  return {
    stores, navigations, run,
    get claimed() { return claimed; },
    get skipped() { return skipped; },
  };
}

test("P006.7.11.15.4_R2 preserves the locked v17 PWA generation ABI", () => {
  assert.match(worker, /^const CACHE_NAME = "nexilabs-shell-v17";/m);
  assert.match(policy, /^export const PWA_CACHE_VERSION = "nexilabs-shell-v17";/m);
  assert.match(worker, /^const SAME_GENERATION_REFRESH_MARKER = "nexilabs-refresh-p006-7-11-15-4-r2";/m);
});

test("P006.7.11.15.4_R2 keeps worker-policy parity and the complete current map graph", () => {
  const workerAssets = parseAssets(worker, "const APP_SHELL");
  const policyAssets = parseAssets(policy, "APPLICATION_SHELL_ASSETS");
  assert.deepEqual(workerAssets, policyAssets);
  assert.equal(new Set(workerAssets).size, workerAssets.length);
  for (const asset of REQUIRED_CURRENT_ASSETS) assert.ok(workerAssets.includes(asset), asset);
});

test("P006.7.11.15.4_R2 refreshes an existing v17 cache and restarts its stale client exactly once", async () => {
  const h = makeHarness(["nexilabs-shell-v17"]);
  h.stores.get("nexilabs-shell-v17").set("./src/main.js", { asset: "STALE_MAIN" });

  await h.run("install");
  assert.equal(h.skipped, 1);
  assert.ok(h.stores.has("nexilabs-shell-v17"));
  assert.ok(h.stores.has("nexilabs-refresh-p006-7-11-15-4-r2"));
  for (const asset of REQUIRED_CURRENT_ASSETS) {
    assert.ok(h.stores.get("nexilabs-shell-v17").has(asset), asset);
  }

  await h.run("activate");
  assert.equal(h.claimed, 1);
  assert.deepEqual(h.navigations, ["http://127.0.0.1:8765/#/simulation/novegeo"]);
  assert.ok(h.stores.has("nexilabs-shell-v17"));
  assert.equal(h.stores.has("nexilabs-refresh-p006-7-11-15-4-r2"), false);
});

test("P006.7.11.15.4_R2 preserves the historical v16 to v17 upgrade path", async () => {
  const h = makeHarness(["nexilabs-shell-v16"]);

  await h.run("install");
  assert.ok(h.stores.has("nexilabs-shell-v16"));
  assert.ok(h.stores.has("nexilabs-shell-v17"));

  await h.run("activate");
  assert.equal(h.stores.has("nexilabs-shell-v16"), false);
  assert.equal(h.stores.has("nexilabs-shell-v17"), true);
  assert.equal(h.claimed, 1);
  assert.deepEqual(h.navigations, ["http://127.0.0.1:8765/#/simulation/novegeo"]);
});

test("P006.7.11.15.4_R2 keeps first installation free of an unnecessary activation navigation", async () => {
  const h = makeHarness([]);

  await h.run("install");
  assert.equal(h.stores.has("nexilabs-refresh-p006-7-11-15-4-r2"), false);

  await h.run("activate");
  assert.equal(h.claimed, 1);
  assert.deepEqual(h.navigations, []);
});
