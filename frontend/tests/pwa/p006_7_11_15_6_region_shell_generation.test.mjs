import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const cachePolicy = readFileSync(resolve(ROOT, "src/pwa/cache-policy.js"), "utf8");
const serviceWorker = readFileSync(resolve(ROOT, "sw.js"), "utf8");
const regionAssets = [
  "./src/app/features/novegeo-region-map-experience.js",
  "./src/map/cartography/region-anchor.js",
  "./src/map/cartography/region-cartographic-overlay.js",
];

function quotedAssets(source) {
  return [...source.matchAll(/^\s*[\"'](\.\/[^\"']+)[\"'],?\s*$/gm)].map((match) => match[1]);
}

test("P006.7.11.15.6 keeps the locked v17 cache ABI and pre-caches all additive REGION modules", () => {
  assert.match(cachePolicy, /PWA_CACHE_VERSION\s*=\s*[\"']nexilabs-shell-v17[\"']/);
  assert.match(serviceWorker, /CACHE_NAME\s*=\s*[\"']nexilabs-shell-v17[\"']/);
  const policyAssets = quotedAssets(cachePolicy);
  const workerAssets = quotedAssets(serviceWorker);
  assert.equal(new Set(policyAssets).size, policyAssets.length, "cache policy contains duplicate assets");
  assert.equal(new Set(workerAssets).size, workerAssets.length, "service worker contains duplicate assets");
  for (const asset of regionAssets) {
    assert.ok(policyAssets.includes(asset), `cache policy missing ${asset}`);
    assert.ok(workerAssets.includes(asset), `service worker missing ${asset}`);
  }
});

test("service worker uses a .15.6 same-generation refresh and mirrors the application-shell asset list", () => {
  assert.match(serviceWorker, /SAME_GENERATION_REFRESH_MARKER = "nexilabs-refresh-p006-7-11-15-4-r2"/);
  assert.match(serviceWorker, /REGION_SAME_GENERATION_REFRESH_MARKER = "nexilabs-refresh-p006-7-11-15-6-r1"/);
  assert.deepEqual(quotedAssets(serviceWorker), quotedAssets(cachePolicy));
  assert.match(serviceWorker, /refreshingExistingGeneration/);
  assert.match(serviceWorker, /client\.navigate\(client\.url\)/);
});


function makeWorkerHarness(initialCacheNames = []) {
  const listeners = new Map();
  const stores = new Map(initialCacheNames.map((name) => [name, new Map()]));
  const navigations = [];
  let claimed = 0;
  let skipped = 0;
  function cacheObject(name) {
    if (!stores.has(name)) stores.set(name, new Map());
    const content = stores.get(name);
    return {
      async addAll(assets) { for (const asset of assets) content.set(asset, { asset, clone() { return this; } }); },
      async put(asset, response) { content.set(asset, response); },
      async match(asset) { return content.get(typeof asset === "string" ? asset : asset.url); },
    };
  }
  const caches = {
    async open(name) { return cacheObject(name); },
    async keys() { return [...stores.keys()]; },
    async delete(name) { return stores.delete(name); },
    async match(request) {
      const key = typeof request === "string" ? request : request.url;
      for (const content of stores.values()) if (content.has(key)) return content.get(key);
      return undefined;
    },
  };
  const self = {
    location: { origin: "http://127.0.0.1:8765" },
    addEventListener(type, listener) { listeners.set(type, listener); },
    async skipWaiting() { skipped += 1; },
    clients: {
      async claim() { claimed += 1; },
      async matchAll() {
        return [
          { url: "http://127.0.0.1:8765/#/simulation/novegeo", async navigate(url) { navigations.push(url); } },
          { url: "https://external.example/", async navigate(url) { navigations.push(url); } },
        ];
      },
    },
  };
  vm.runInNewContext(serviceWorker, {
    self, caches, URL, AbortController, setTimeout, clearTimeout,
    fetch: async () => { throw new Error("network not expected"); },
  });
  async function run(type) {
    let promise;
    listeners.get(type)({ waitUntil(value) { promise = value; } });
    await promise;
  }
  return { stores, navigations, run, get claimed() { return claimed; }, get skipped() { return skipped; } };
}

test(".15.6 refresh remains backward-compatible with the locked .15.4 v17 marker contract", async () => {
  const harness = makeWorkerHarness(["nexilabs-shell-v17"]);
  await harness.run("install");
  assert.equal(harness.skipped, 1);
  assert.ok(harness.stores.has("nexilabs-refresh-p006-7-11-15-4-r2"));
  assert.ok(harness.stores.has("nexilabs-refresh-p006-7-11-15-6-r1"));
  for (const asset of regionAssets) assert.ok(harness.stores.get("nexilabs-shell-v17").has(asset), asset);
  await harness.run("activate");
  assert.equal(harness.claimed, 1);
  assert.deepEqual(harness.navigations, ["http://127.0.0.1:8765/#/simulation/novegeo"]);
  assert.equal(harness.stores.has("nexilabs-refresh-p006-7-11-15-4-r2"), false);
  assert.equal(harness.stores.has("nexilabs-refresh-p006-7-11-15-6-r1"), false);
  assert.ok(harness.stores.has("nexilabs-shell-v17"));
});

test("fresh .15.6 installation performs no unnecessary activation navigation", async () => {
  const harness = makeWorkerHarness([]);
  await harness.run("install");
  assert.equal(harness.stores.has("nexilabs-refresh-p006-7-11-15-4-r2"), false);
  assert.equal(harness.stores.has("nexilabs-refresh-p006-7-11-15-6-r1"), false);
  await harness.run("activate");
  assert.equal(harness.claimed, 1);
  assert.deepEqual(harness.navigations, []);
});
