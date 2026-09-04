import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const worker = readFileSync(new URL("../../sw.js", import.meta.url), "utf8");
const policy = readFileSync(new URL("../../src/pwa/cache-policy.js", import.meta.url), "utf8");
const compositorAsset = "./src/map/cartography/unified-environmental-compositor.js";
const marker = "nexilabs-refresh-p006-7-11-15-10-1-3";

test(".15.10.1.3 preserves the v17 cache ABI and caches the unified environmental compositor", () => {
  assert.match(worker, /CACHE_NAME = "nexilabs-shell-v17"/);
  assert.match(policy, /PWA_CACHE_VERSION = "nexilabs-shell-v17"/);
  assert.ok(worker.includes(`"${compositorAsset}"`));
  assert.ok(policy.includes(`"${compositorAsset}"`));
  assert.ok(worker.includes(marker));
  assert.match(worker, /UNIFIED_ENVIRONMENTAL_COMPOSITION_SAME_GENERATION_REFRESH_MARKER/);
});

test("an existing v17 client receives the .15.10.1.3 shell graph and one automatic navigation handoff", async () => {
  const listeners = new Map();
  const stores = new Map([["nexilabs-shell-v17", new Map([[compositorAsset, "stale-compositor"]])]]);
  let navigations = 0;
  const cache = (name) => ({
    async addAll(assets) { for (const asset of assets) stores.get(name).set(asset, `fresh:${asset}`); },
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
      async matchAll() {
        return [{
          url: "http://127.0.0.1:8765/#/simulation/novegeo",
          async navigate() { navigations += 1; },
        }];
      },
    },
  };

  vm.runInNewContext(worker, {
    self, caches, URL, AbortController, setTimeout, clearTimeout,
    fetch: async () => { throw new Error("network not expected"); },
  });

  const run = async (type) => {
    let pending;
    listeners.get(type)({ waitUntil(value) { pending = value; } });
    await pending;
  };

  await run("install");
  assert.ok(stores.has(marker));
  assert.equal(stores.get("nexilabs-shell-v17").get(compositorAsset), `fresh:${compositorAsset}`);

  await run("activate");
  assert.equal(navigations, 1);
  assert.deepEqual([...stores.keys()], ["nexilabs-shell-v17"]);
});
