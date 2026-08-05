/** P003.5 — In-memory service-worker behaviour simulator for deterministic tests. */
export class MemoryCacheStorage {
  constructor(initial = {}) { this.caches = new Map(Object.entries(initial).map(([name, entries]) => [name, new Map(Object.entries(entries))])); }
  async open(name) { if (!this.caches.has(name)) this.caches.set(name, new Map()); const store = this.caches.get(name); return { addAll: async (assets) => assets.forEach((asset) => store.set(asset, `cached:${asset}`)), match: async (key) => store.get(key), put: async (key, value) => store.set(key, value) }; }
  async match(key) { for (const store of this.caches.values()) if (store.has(key)) return store.get(key); return undefined; }
  async keys() { return [...this.caches.keys()]; }
  async delete(name) { return this.caches.delete(name); }
}

export async function simulateOfflineQualification({ cacheStorage, cacheName, shellAssets, offlineDocument }) {
  const cache = await cacheStorage.open(cacheName);
  await cache.addAll(shellAssets);
  const offlineResponse = await cacheStorage.match(offlineDocument);
  return Object.freeze({ cacheName, cachedAssetCount: shellAssets.length, offlineDocument, offlineResponse, passed: Boolean(offlineResponse) });
}

export async function simulateActivationCleanup(cacheStorage, currentCacheName) {
  const before = await cacheStorage.keys();
  await Promise.all(before.filter((name) => name !== currentCacheName).map((name) => cacheStorage.delete(name)));
  const after = await cacheStorage.keys();
  return Object.freeze({ before, after, passed: after.length === 1 && after[0] === currentCacheName });
}
