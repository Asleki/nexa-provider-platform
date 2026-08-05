import test from "node:test";
import assert from "node:assert/strict";
import { MemoryCacheStorage, simulateActivationCleanup, simulateOfflineQualification } from "../../src/pwa/qualification/offline-simulator.js";

test("offline document is available after shell pre-cache", async () => {
  const storage = new MemoryCacheStorage();
  const result = await simulateOfflineQualification({ cacheStorage: storage, cacheName: "current", shellAssets: ["./index.html", "./app.js"], offlineDocument: "./index.html" });
  assert.equal(result.passed, true);
  assert.equal(result.cachedAssetCount, 2);
});

test("activation cleanup removes stale caches", async () => {
  const storage = new MemoryCacheStorage({ old: {}, current: {} });
  const result = await simulateActivationCleanup(storage, "current");
  assert.deepEqual(result.after, ["current"]);
  assert.equal(result.passed, true);
});
