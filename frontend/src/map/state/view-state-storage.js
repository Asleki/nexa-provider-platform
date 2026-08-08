/** P006.4 — safe browser persistence for presentation-only map view state. */
import { MAP_VIEW_STATE_VERSION, validateMapViewState } from "./view-state-contracts.js";

const STORAGE_PREFIX = "nexilabs:novegeo:map-view";

export function mapViewStateStorageKey(runtimeMode) {
  const mode = String(runtimeMode ?? "").trim();
  if (!mode) throw new TypeError("runtimeMode is required");
  return `${STORAGE_PREFIX}:v${MAP_VIEW_STATE_VERSION}:${mode}`;
}

export function createMapViewStateRepository({ storage, runtimeMode } = {}) {
  const key = mapViewStateStorageKey(runtimeMode);
  const available = storage && typeof storage.getItem === "function" && typeof storage.setItem === "function" && typeof storage.removeItem === "function";

  return Object.freeze({
    key,
    available: Boolean(available),
    load() {
      if (!available) return Object.freeze({ status: "UNAVAILABLE", state: null });
      const raw = storage.getItem(key);
      if (!raw) return Object.freeze({ status: "EMPTY", state: null });
      try {
        const state = validateMapViewState(JSON.parse(raw), { runtimeMode });
        return Object.freeze({ status: "RESTORED", state });
      } catch (error) {
        storage.removeItem(key);
        return Object.freeze({ status: "REJECTED", state: null, reason: error instanceof Error ? error.message : String(error) });
      }
    },
    save(state) {
      if (!available) return Object.freeze({ status: "UNAVAILABLE" });
      const normalized = validateMapViewState(state, { runtimeMode });
      storage.setItem(key, JSON.stringify(normalized));
      return Object.freeze({ status: "SAVED", revision: normalized.revision });
    },
    clear() {
      if (!available) return Object.freeze({ status: "UNAVAILABLE" });
      storage.removeItem(key);
      return Object.freeze({ status: "CLEARED" });
    },
  });
}
