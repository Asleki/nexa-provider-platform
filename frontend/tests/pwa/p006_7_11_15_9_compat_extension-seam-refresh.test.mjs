import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const serviceWorker = readFileSync(resolve(ROOT, "sw.js"), "utf8");

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
    self,
    caches,
    URL,
    AbortController,
    setTimeout,
    clearTimeout,
    fetch: async () => { throw new Error("network not expected"); },
  });
  async function run(type) {
    let promise;
    listeners.get(type)({ waitUntil(value) { promise = value; } });
    await promise;
  }
  return { stores, navigations, run, get claimed() { return claimed; }, get skipped() { return skipped; } };
}


test("compatibility seam preserves v17 and all locked REGION/CITY refresh markers", () => {
  assert.match(serviceWorker, /CACHE_NAME = "nexilabs-shell-v17"/);
  assert.match(serviceWorker, /nexilabs-refresh-p006-7-11-15-4-r2/);
  assert.match(serviceWorker, /nexilabs-refresh-p006-7-11-15-6-r1/);
  assert.match(serviceWorker, /nexilabs-refresh-p006-7-11-15-7-r1/);
  assert.match(serviceWorker, /MAP_EXTENSION_SEAM_SAME_GENERATION_REFRESH_MARKER = "nexilabs-refresh-p006-7-11-15-9-compat-seam-r1"/);
});


test("existing v17 client receives one same-generation seam refresh", async () => {
  const harness = makeWorkerHarness(["nexilabs-shell-v17"]);
  await harness.run("install");
  assert.equal(harness.skipped, 1);
  assert.ok(harness.stores.has("nexilabs-refresh-p006-7-11-15-9-compat-seam-r1"));
  await harness.run("activate");
  assert.equal(harness.claimed, 1);
  assert.deepEqual(harness.navigations, ["http://127.0.0.1:8765/#/simulation/novegeo"]);
});
