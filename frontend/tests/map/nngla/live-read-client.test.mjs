import test from "node:test";
import assert from "node:assert/strict";
import { createLiveNnglaReadClient } from "../../../src/map/nngla/live-read-client.js";

const families = [
  ["PLACE", 700, 700], ["ADMINISTRATIVE_AREA", 192, 192], ["GEOGRAPHIC_FEATURE", 21, 21],
  ["ROAD", 900, 350], ["ADDRESS", 0, 0], ["PARCEL", 0, 0],
].map(([family, sourceCount, canonicalCount]) => ({ family, sourceCount, canonicalCount, publishedCount: 0, mapRenderableCount: 0 }));

test("Bundle 18 live NNGLA client keeps browser access on GET-only /api/v1/nngla", async () => {
  const calls = [];
  const fetchRef = async (url, options) => {
    calls.push([url, options]);
    if (url.endsWith("/status")) return { ok: true, status: 200, async json() { return { authorityId: "authority:nngla", countryId: "country:novegeo", databaseAuthority: "SERVER_SIDE_ONLY", liveDatabaseMigrationStatus: "EXECUTED", readRuntime: "simulation", readModelVersion: 1, families }; } };
    return { ok: true, status: 200, async json() { return { family: "PLACE", count: 0, sourceCount: 700, canonicalCount: 700, publishedCount: 0, mapRenderableCount: 0, readRuntime: "simulation", readModelVersion: 1, items: [] }; } };
  };
  const client = createLiveNnglaReadClient({ apiBaseUrl: "http://localhost:8000", fetchRef });
  assert.equal((await client.status()).liveDatabaseMigrationStatus, "EXECUTED");
  assert.equal((await client.list("places")).canonicalCount, 700);
  assert.deepEqual(calls.map(([url]) => url), ["http://localhost:8000/api/v1/nngla/status", "http://localhost:8000/api/v1/nngla/places"]);
  assert.ok(calls.every(([, options]) => options.method === "GET"));
});
