import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";

const worker = readFileSync(new URL("../../sw.js", import.meta.url), "utf8");
const policy = readFileSync(new URL("../../src/pwa/cache-policy.js", import.meta.url), "utf8");

const cacheName = "nexilabs-shell-v17";
const marker = "nexilabs-refresh-p006-ui-10-1-r2";
const mainAsset = "./src/main.js";
const accountAssets = Object.freeze([
  "./styles/account-enrollment-v1.css",
  "./src/app/account/account-enrollment-route.js",
  "./src/app/account/account-enrollment-experience.js",
  "./src/ui/pages/account-enrollment-gateway.js",
  "./src/ui/pages/guest-account-enrollment.js",
  "./src/ui/pages/developer-account-enrollment.js",
]);

test("P006.UI.10.1.R2 preserves the v17 cache ABI and closes the account-enrollment shell graph", () => {
  assert.match(worker, /CACHE_NAME = "nexilabs-shell-v17"/);
  assert.match(policy, /PWA_CACHE_VERSION = "nexilabs-shell-v17"/);
  assert.ok(worker.includes(`"${mainAsset}"`));
  assert.ok(policy.includes(`"${mainAsset}"`));
  for (const asset of accountAssets) {
    assert.ok(worker.includes(`"${asset}"`), `worker missing ${asset}`);
    assert.ok(policy.includes(`"${asset}"`), `policy missing ${asset}`);
  }
  assert.ok(worker.includes(marker));
  assert.match(worker, /ACCOUNT_ENROLLMENT_ACTIVATION_SAME_GENERATION_REFRESH_MARKER/);
  assert.match(worker, /client\.navigate\(client\.url\)/);
});

test("an existing installed v17 client receives fresh main plus the account graph and one navigation handoff", async () => {
  const listeners = new Map();
  const stores = new Map([[cacheName, new Map([[mainAsset, "stale-main"]])]]);
  let navigations = 0;
  let claims = 0;
  let skipWaitingCalls = 0;

  const cache = (name) => ({
    async addAll(assets) {
      const store = stores.get(name);
      for (const asset of assets) store.set(asset, `fresh:${asset}`);
    },
    async put(key, value) { stores.get(name).set(key, value); },
    async match(key) { return stores.get(name).get(key); },
  });

  const caches = {
    async keys() { return [...stores.keys()]; },
    async open(name) {
      if (!stores.has(name)) stores.set(name, new Map());
      return cache(name);
    },
    async delete(name) { return stores.delete(name); },
    async match() { return undefined; },
  };

  const self = {
    location: { origin: "http://127.0.0.1:8765" },
    addEventListener(type, listener) { listeners.set(type, listener); },
    async skipWaiting() { skipWaitingCalls += 1; },
    clients: {
      async claim() { claims += 1; },
      async matchAll() {
        return [
          {
            url: "http://127.0.0.1:8765/#/runtime",
            async navigate() { navigations += 1; },
          },
          {
            url: "https://example.invalid/foreign-client",
            async navigate() { throw new Error("foreign client must not navigate"); },
          },
        ];
      },
    },
  };

  vm.runInNewContext(worker, {
    self,
    caches,
    URL,
    AbortController,
    setTimeout,
    clearTimeout,
    fetch: async () => { throw new Error("network not expected during install/activate simulation"); },
  });

  const run = async (type) => {
    let pending;
    listeners.get(type)({ waitUntil(value) { pending = value; } });
    await pending;
  };

  await run("install");

  assert.equal(skipWaitingCalls, 1);
  assert.ok(stores.has(marker));
  assert.equal(stores.get(cacheName).get(mainAsset), `fresh:${mainAsset}`);
  for (const asset of accountAssets) {
    assert.equal(stores.get(cacheName).get(asset), `fresh:${asset}`);
  }

  await run("activate");

  assert.equal(claims, 1);
  assert.equal(navigations, 1);
  assert.deepEqual([...stores.keys()], [cacheName]);
});

test("R2 does not cache private development authentication fixtures", () => {
  const combined = `${worker}\n${policy}`;
  for (const forbidden of [
    "development/auth/private",
    "guests.local.json",
    "developers.local.json",
    "enigma_words_3.csv",
    "enigma_words_4.csv",
    "enigma_words_5.csv",
  ]) {
    assert.ok(!combined.includes(forbidden), forbidden);
  }
});
