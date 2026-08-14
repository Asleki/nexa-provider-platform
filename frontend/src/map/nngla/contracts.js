/** P006.7.9 / Bundle 15.0D — Public NNGLA read-model contracts. */
export const NnglaReadStatus = Object.freeze({ READY: "READY", DEGRADED: "DEGRADED", OFFLINE: "OFFLINE" });

export function assertPublicNnglaStatus(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) throw new TypeError("NNGLA status payload must be an object");
  if (payload.authorityId !== "authority:nngla" || payload.countryId !== "country:novegeo") throw new Error("NNGLA authority identity mismatch");
  if (payload.databaseAuthority !== "SERVER_SIDE_ONLY") throw new Error("NNGLA browser/database authority boundary violated");
  if (payload.liveDatabaseMigrationStatus !== "NOT_EXECUTED") throw new Error("NNGLA migration truth is required before live migration");
  if (!Array.isArray(payload.families)) throw new Error("NNGLA family summaries are required");
  for (const item of payload.families) {
    for (const key of ["sourceCount", "canonicalCount", "publishedCount", "mapRenderableCount"]) {
      if (!Number.isInteger(item?.[key]) || item[key] < 0) throw new Error(`Invalid NNGLA family ${key}`);
    }
    if (!item.family || item.canonicalCount > item.sourceCount || item.publishedCount > item.canonicalCount || item.mapRenderableCount > item.publishedCount) throw new Error("Inconsistent NNGLA family counts");
  }
  return payload;
}

export function assertPublicNnglaFamily(payload) {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) throw new TypeError("NNGLA family payload must be an object");
  if (!Array.isArray(payload.items)) throw new Error("NNGLA family items are required");
  for (const item of payload.items) {
    if (item.publicEligible !== true) throw new Error("Public NNGLA payload contains an ineligible item");
    if (item.mapRenderable && !item.geometryReference) throw new Error("Map-renderable NNGLA item requires geometryReference");
    if ("holderReference" in item || "titleHolder" in item) throw new Error("Private title-holder fields are forbidden in public NNGLA payloads");
  }
  return payload;
}
