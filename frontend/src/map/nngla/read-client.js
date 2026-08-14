/** P006.7.9 — Read-only browser client for NNGLA public read models. */
import { assertPublicNnglaFamily, assertPublicNnglaStatus } from "./contracts.js";

function normalizeBaseUrl(value) {
  const text = String(value ?? "").trim();
  if (!text) return "";
  return text.replace(/\/$/, "");
}

async function readJson(fetchRef, url, validator) {
  const response = await fetchRef(url, { method: "GET", headers: { accept: "application/json" } });
  if (!response?.ok) throw new Error(`NNGLA read request failed (${response?.status ?? "unknown"})`);
  return validator(await response.json());
}

export function createNnglaReadClient({ apiBaseUrl = "", fetchRef = globalThis.fetch } = {}) {
  if (typeof fetchRef !== "function") throw new TypeError("fetchRef must be a function");
  const base = normalizeBaseUrl(apiBaseUrl);
  const endpoint = (path) => `${base}/api/v1/nngla${path}`;
  return Object.freeze({
    apiBaseUrl: base,
    async status() { return readJson(fetchRef, endpoint("/status"), assertPublicNnglaStatus); },
    async list(familyPath) {
      const allowed = new Set(["places", "features", "administrative-areas", "roads", "addresses", "parcels"]);
      if (!allowed.has(familyPath)) throw new Error(`Unsupported NNGLA family path: ${familyPath}`);
      return readJson(fetchRef, endpoint(`/${familyPath}`), assertPublicNnglaFamily);
    },
  });
}
