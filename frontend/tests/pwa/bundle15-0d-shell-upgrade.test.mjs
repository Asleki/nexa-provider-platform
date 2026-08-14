import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const workerSource = readFileSync(resolve(ROOT, "sw.js"), "utf8");

function workerHarness() {
  const listeners = new Map();
  const stores = new Map([["nexilabs-shell-v16", { legacy: true }]]);
  const navigations = [];
  let claimed = 0;
  let skipped = 0;
  const cacheObject = (name) => ({
    async addAll(assets) { stores.set(name, { assets: [...assets] }); },
    async put() {},
  });
  const caches = {
    async open(name) { return cacheObject(name); },
    async keys() { return [...stores.keys()]; },
    async delete(name) { return stores.delete(name); },
    async match() { return undefined; },
  };
  const self = {
    location: { origin: "http://127.0.0.1:8765" },
    addEventListener(type, fn) { listeners.set(type, fn); },
    async skipWaiting() { skipped += 1; },
    clients: {
      async claim() { claimed += 1; },
      async matchAll() { return [
        { url: "http://127.0.0.1:8765/#/simulation/novegeo", async navigate(url) { navigations.push(url); } },
        { url: "https://external.example/", async navigate(url) { navigations.push(url); } },
      ]; },
    },
  };
  vm.runInNewContext(workerSource, { self, caches, fetch: async () => { throw new Error("network not expected"); }, URL, AbortController, setTimeout, clearTimeout });
  async function run(type) {
    let promise;
    listeners.get(type)({ waitUntil(value) { promise = value; } });
    await promise;
  }
  return { stores, navigations, run, get claimed() { return claimed; }, get skipped() { return skipped; } };
}

test("Bundle 15.0D upgrades an installed v16 shell to v17 without manual storage clearing", async () => {
  const h = workerHarness();
  await h.run("install");
  assert.ok(h.stores.has("nexilabs-shell-v16"));
  assert.ok(h.stores.has("nexilabs-shell-v17"));
  const assets = h.stores.get("nexilabs-shell-v17").assets;
  for (const required of [
    "./src/app/features/novegeo-feature-runtime.js",
    "./src/map/nngla/contracts.js",
    "./src/map/nngla/read-client.js",
    "./src/map/nngla/render-plan.js",
    "./src/map/nngla/publication-status.js",
  ]) assert.ok(assets.includes(required), required);
  assert.equal(h.skipped, 1);

  await h.run("activate");
  assert.equal(h.stores.has("nexilabs-shell-v16"), false);
  assert.equal(h.stores.has("nexilabs-shell-v17"), true);
  assert.equal(h.claimed, 1);
  assert.deepEqual(h.navigations, ["http://127.0.0.1:8765/#/simulation/novegeo"]);
});

test("Bundle 15.0D NNGLA shell graph contains no private title or database credential material", () => {
  assert.doesNotMatch(workerSource, /holderReference|titleHolder|postgres(?:ql)?:\/\/|password=/i);
});
