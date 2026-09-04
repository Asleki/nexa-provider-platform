/**
 * P006.7.11.15.10.1 — shared governed NoveGeo snapshot transport.
 *
 * This module owns no geography or publication policy. It only coalesces the
 * authoritative sovereign-boundary read and the first complete national-map
 * viewport read so every presentation consumer observes one governed snapshot.
 */

const SHARED_SNAPSHOT_TTL_MS = 30_000;
const sessionsByFetch = new WeakMap();

function normalizedBase(value) {
  const base = String(value ?? "").trim().replace(/\/$/, "");
  if (!base) throw new Error("apiBaseUrl is required for governed NoveGeo snapshot loading");
  return base;
}

function finiteBounds(bounds) {
  const keys = ["minLongitude", "minLatitude", "maxLongitude", "maxLatitude"];
  const normalized = {};
  for (const key of keys) {
    const value = Number(bounds?.[key]);
    if (!Number.isFinite(value)) throw new TypeError(`missing ${key}`);
    normalized[key] = value;
  }
  if (!(normalized.minLongitude < normalized.maxLongitude && normalized.minLatitude < normalized.maxLatitude)) {
    throw new RangeError("invalid national map bounds");
  }
  return Object.freeze(normalized);
}

function boundsKey(bounds) {
  const value = finiteBounds(bounds);
  return [value.minLongitude, value.minLatitude, value.maxLongitude, value.maxLatitude].join("|");
}

function sessionFor(fetchRef, apiBaseUrl) {
  if (typeof fetchRef !== "function") throw new TypeError("fetchRef must be a function");
  const base = normalizedBase(apiBaseUrl);
  let byBase = sessionsByFetch.get(fetchRef);
  if (!byBase) {
    byBase = new Map();
    sessionsByFetch.set(fetchRef, byBase);
  }
  if (!byBase.has(base)) {
    byBase.set(base, {
      base,
      boundary: { value: null, promise: null, expiresAt: 0 },
      maps: new Map(),
    });
  }
  return byBase.get(base);
}

async function jsonGet(fetchRef, url) {
  const response = await fetchRef(url, { method: "GET", headers: { accept: "application/json" } });
  if (!response?.ok) throw new Error(`governed snapshot read failed (${response?.status ?? "unknown"})`);
  return response.json();
}

function cachedRead(slot, load) {
  const now = Date.now();
  if (slot.value !== null && slot.expiresAt > now) return Promise.resolve(slot.value);
  if (slot.promise) return slot.promise;
  slot.promise = Promise.resolve()
    .then(load)
    .then((value) => {
      slot.value = value;
      slot.expiresAt = Date.now() + SHARED_SNAPSHOT_TTL_MS;
      return value;
    })
    .catch((error) => {
      slot.value = null;
      slot.expiresAt = 0;
      throw error;
    })
    .finally(() => {
      slot.promise = null;
    });
  return slot.promise;
}

export function createGovernedSnapshotLoader({ apiBaseUrl = "", fetchRef = globalThis.fetch } = {}) {
  const session = sessionFor(fetchRef, apiBaseUrl);

  return Object.freeze({
    apiBaseUrl: session.base,

    readBoundaryRaw() {
      return cachedRead(
        session.boundary,
        () => jsonGet(fetchRef, `${session.base}/api/v1/geography/world-boundary`),
      );
    },

    readCompleteMapViewportRaw(bounds) {
      const normalized = finiteBounds(bounds);
      const key = boundsKey(normalized);
      let slot = session.maps.get(key);
      if (!slot) {
        slot = { value: null, promise: null, expiresAt: 0 };
        session.maps.set(key, slot);
      }
      return cachedRead(slot, () => {
        const params = new URLSearchParams();
        params.set("minLongitude", String(normalized.minLongitude));
        params.set("minLatitude", String(normalized.minLatitude));
        params.set("maxLongitude", String(normalized.maxLongitude));
        params.set("maxLatitude", String(normalized.maxLatitude));
        params.set("limit", "2000");
        // Deliberately no family filter: the existing endpoint returns the one
        // governed snapshot that presentation consumers partition locally.
        return jsonGet(fetchRef, `${session.base}/api/v1/nngla-map/features?${params}`);
      });
    },
  });
}

export function resetGovernedSnapshotLoaderForTests() {
  // WeakMap cannot be cleared in place. Test isolation is achieved by using a
  // fresh fetch function, which creates a distinct weak-keyed session.
  return true;
}

export { SHARED_SNAPSHOT_TTL_MS };
