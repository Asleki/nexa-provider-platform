/** P006.7.11.9 / P006.7.11.15.10.1 — HTTP-only authoritative NoveGeo boundary reader. */
import { validateWorldBoundaryPublication } from "./contracts.js";
import { createGovernedSnapshotLoader } from "../nngla/governed-snapshot-loader.js";

export const LIVE_NOVEGEO_BOUNDARY = Object.freeze({
  boundaryId: "boundary:novegeo:sovereign",
  boundaryVersion: 2,
  datasetId: "dataset:novegeo:world-boundary",
  datasetVersion: 2,
  runtimeMode: "shared_reference",
});

function normalizeBaseUrl(value) {
  return String(value ?? "").trim().replace(/\/$/, "");
}

export function assertLiveWorldBoundaryPublication(payload) {
  const value = validateWorldBoundaryPublication(payload);
  for (const [key, expected] of Object.entries(LIVE_NOVEGEO_BOUNDARY)) {
    if (value[key] !== expected) throw new Error(`live world boundary ${key} mismatch`);
  }
  if (!String(value.publicationId || "").startsWith("publication:novegeo:world-boundary:")) {
    throw new Error("live world boundary publicationId mismatch");
  }
  if (!/^[0-9a-f]{64}$/i.test(String(value.sourceSha256 || ""))) throw new Error("live world boundary sourceSha256 is invalid");
  if (!/^[0-9a-f]{64}$/i.test(String(value.contentSha256 || ""))) throw new Error("live world boundary contentSha256 is invalid");
  return value;
}

export function createLiveWorldBoundaryClient({ apiBaseUrl, fetchRef = globalThis.fetch } = {}) {
  if (typeof fetchRef !== "function") throw new TypeError("fetchRef must be a function");
  const base = normalizeBaseUrl(apiBaseUrl);
  if (!base) throw new Error("apiBaseUrl is required for live boundary authority");
  const url = `${base}/api/v1/geography/world-boundary`;
  const loader = createGovernedSnapshotLoader({ apiBaseUrl: base, fetchRef });
  return Object.freeze({
    apiBaseUrl: base,
    endpoint: url,
    async getActive() {
      return assertLiveWorldBoundaryPublication(await loader.readBoundaryRaw());
    },
  });
}
