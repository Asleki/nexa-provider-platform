import test from "node:test";
import assert from "node:assert/strict";
import {
  assertLiveWorldBoundaryPublication,
  createLiveWorldBoundaryClient,
} from "../../../src/map/geography/live-boundary-client.js";

function boundary(overrides = {}) {
  return {
    publicationId: "publication:novegeo:world-boundary:v002",
    boundaryId: "boundary:novegeo:sovereign",
    boundaryVersion: 2,
    datasetId: "dataset:novegeo:world-boundary",
    datasetVersion: 2,
    coordinateReference: {
      coordinateReferenceId: "crs:novegeo:geographic",
      version: 1,
      authorityName: "EPSG",
      authorityCode: "4326",
      axisOrder: ["longitude", "latitude"],
      unit: "decimal_degrees",
    },
    geometry: { type: "MultiPolygon", coordinates: [[[[29.05, -1], [30, -1], [30, 1], [29.05, -1]]]] },
    extent: { minLongitude: 29.05, minLatitude: -7.717467, maxLongitude: 44.805229, maxLatitude: 7.85 },
    sourceSha256: "a".repeat(64),
    contentSha256: "b".repeat(64),
    runtimeMode: "shared_reference",
    ...overrides,
  };
}

test("Bundle 18 live boundary contract accepts only sovereign PostgreSQL v002 semantics", () => {
  assert.equal(assertLiveWorldBoundaryPublication(boundary()).boundaryVersion, 2);
  assert.throws(() => assertLiveWorldBoundaryPublication(boundary({ boundaryVersion: 1 })), /boundaryVersion mismatch/);
  assert.throws(() => assertLiveWorldBoundaryPublication(boundary({ runtimeMode: "simulation" })), /runtimeMode mismatch/);
});

test("Bundle 18 boundary client uses the existing HTTP API route and never a static fallback", async () => {
  const calls = [];
  const client = createLiveWorldBoundaryClient({
    apiBaseUrl: "http://localhost:8000/",
    fetchRef: async (url, options) => {
      calls.push([url, options]);
      return { ok: true, status: 200, async json() { return boundary(); } };
    },
  });
  const result = await client.getActive();
  assert.equal(result.datasetVersion, 2);
  assert.equal(calls[0][0], "http://localhost:8000/api/v1/geography/world-boundary");
  assert.equal(calls[0][1].method, "GET");
});

test("Bundle 18 boundary client fails closed when API authority is unavailable", async () => {
  const client = createLiveWorldBoundaryClient({
    apiBaseUrl: "http://localhost:8000",
    fetchRef: async () => ({ ok: false, status: 503 }),
  });
  await assert.rejects(() => client.getActive(), /failed \(503\)/);
});
