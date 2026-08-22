/** P006.7.11.9 — HTTP-only client for PostgreSQL-backed NNGLA public read models. */
import { assertLiveNnglaFamily, assertLiveNnglaStatus } from "./live-contracts.js";

const FAMILY_PATHS = Object.freeze({
  places: "PLACE",
  features: "GEOGRAPHIC_FEATURE",
  "administrative-areas": "ADMINISTRATIVE_AREA",
  roads: "ROAD",
  addresses: "ADDRESS",
  parcels: "PARCEL",
});

function normalizeBaseUrl(value) {
  return String(value ?? "").trim().replace(/\/$/, "");
}

async function readJson(fetchRef, url, validator) {
  const response = await fetchRef(url, { method: "GET", headers: { accept: "application/json" } });
  if (!response?.ok) throw new Error(`NNGLA live read request failed (${response?.status ?? "unknown"})`);
  return validator(await response.json());
}

export function createLiveNnglaReadClient({ apiBaseUrl, fetchRef = globalThis.fetch } = {}) {
  if (typeof fetchRef !== "function") throw new TypeError("fetchRef must be a function");
  const base = normalizeBaseUrl(apiBaseUrl);
  if (!base) throw new Error("apiBaseUrl is required for live NNGLA authority");
  const endpoint = (path) => `${base}/api/v1/nngla${path}`;
  return Object.freeze({
    apiBaseUrl: base,
    async status() { return readJson(fetchRef, endpoint("/status"), assertLiveNnglaStatus); },
    async list(familyPath) {
      const expectedFamily = FAMILY_PATHS[familyPath];
      if (!expectedFamily) throw new Error(`Unsupported NNGLA family path: ${familyPath}`);
      return readJson(fetchRef, endpoint(`/${familyPath}`), (payload) => assertLiveNnglaFamily(payload, expectedFamily));
    },
  });
}
