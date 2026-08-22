/** P006.7.11.9 — Additive NNGLA live-database browser contracts. */

export const LiveNnglaMigrationStatus = Object.freeze({ EXECUTED: "EXECUTED" });
export const LiveNnglaReadRuntime = Object.freeze({ SIMULATION: "simulation", PRODUCTION: "production" });
export const LIVE_NNGLA_FAMILIES = Object.freeze([
  "PLACE",
  "ADMINISTRATIVE_AREA",
  "GEOGRAPHIC_FEATURE",
  "ROAD",
  "ADDRESS",
  "PARCEL",
]);

function assertCounts(item, label = "NNGLA family") {
  for (const key of ["sourceCount", "canonicalCount", "publishedCount", "mapRenderableCount"]) {
    if (!Number.isInteger(item?.[key]) || item[key] < 0) throw new Error(`Invalid ${label} ${key}`);
  }
  if (item.canonicalCount > item.sourceCount || item.publishedCount > item.canonicalCount || item.mapRenderableCount > item.publishedCount) {
    throw new Error(`Inconsistent ${label} counts`);
  }
}

function assertReadRuntime(value) {
  if (![LiveNnglaReadRuntime.SIMULATION, LiveNnglaReadRuntime.PRODUCTION].includes(value)) throw new Error("NNGLA live readRuntime is invalid");
}

export function assertLiveNnglaStatus(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) throw new TypeError("NNGLA live status payload must be an object");
  if (payload.authorityId !== "authority:nngla" || payload.countryId !== "country:novegeo") throw new Error("NNGLA authority identity mismatch");
  if (payload.databaseAuthority !== "SERVER_SIDE_ONLY") throw new Error("NNGLA browser/database authority boundary violated");
  if (payload.liveDatabaseMigrationStatus !== LiveNnglaMigrationStatus.EXECUTED) throw new Error("NNGLA live database migration must be EXECUTED");
  assertReadRuntime(payload.readRuntime);
  if (!Number.isInteger(payload.readModelVersion) || payload.readModelVersion < 1) throw new Error("NNGLA readModelVersion is invalid");
  if (!Array.isArray(payload.families)) throw new Error("NNGLA family summaries are required");
  const observed = new Set();
  for (const item of payload.families) {
    if (!LIVE_NNGLA_FAMILIES.includes(item?.family)) throw new Error(`Unsupported live NNGLA family: ${item?.family}`);
    if (observed.has(item.family)) throw new Error(`Duplicate live NNGLA family: ${item.family}`);
    observed.add(item.family);
    assertCounts(item);
  }
  for (const family of LIVE_NNGLA_FAMILIES) if (!observed.has(family)) throw new Error(`Missing live NNGLA family: ${family}`);
  return payload;
}

export function assertLiveNnglaFamily(payload, expectedFamily = null) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) throw new TypeError("NNGLA live family payload must be an object");
  if (!LIVE_NNGLA_FAMILIES.includes(payload.family)) throw new Error("NNGLA live family is unsupported");
  if (expectedFamily && payload.family !== expectedFamily) throw new Error("NNGLA live family response mismatch");
  assertReadRuntime(payload.readRuntime);
  assertCounts(payload, "NNGLA live family");
  if (!Array.isArray(payload.items) || payload.count !== payload.items.length) throw new Error("NNGLA live family items/count mismatch");
  for (const item of payload.items) {
    if (item.publicEligible !== true) throw new Error("Live NNGLA payload contains an ineligible item");
    if (item.family !== payload.family) throw new Error("Live NNGLA item family mismatch");
    if (item.runtimeMode !== payload.readRuntime) throw new Error("Live NNGLA runtime scope mismatch");
    if (item.mapRenderable && !item.geometryReference) throw new Error("Map-renderable live NNGLA item requires geometryReference");
    if (!item.publicationReference) throw new Error("Live NNGLA public item requires publicationReference");
    for (const forbidden of ["holderReference", "titleHolder", "pgHost", "pgUser", "pgPassword", "sql"]) {
      if (forbidden in item) throw new Error(`Forbidden live NNGLA field: ${forbidden}`);
    }
  }
  return payload;
}
